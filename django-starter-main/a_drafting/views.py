# drafting/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Cube, Card, Draft, CubeCard, DraftPlayer, DeckList, CardImage, CubeImage, DraftPack
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    CubeSerializer, CardSerializer, DraftSerializer, 
    DraftPlayerSerializer, DeckListSerializer
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import requests
import logging
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.urls import reverse
from random import sample
from collections import Counter
from random import shuffle
from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.utils.text import slugify

logger = logging.getLogger(__name__)

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
class DraftViewSet(viewsets.ModelViewSet):
    queryset = Draft.objects.filter(active=True)
    serializer_class = DraftSerializer

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def create_lobby(self, request):
        user = request.user
        data = request.data

        cube_id = data.get("cube_id")
        pack_count = data.get("pack_count", 3)
        cards_per_pack = data.get("cards_per_pack", 15)
        max_players = data.get("max_players", 8)

        try:
            cube = Cube.objects.get(id=cube_id)
            draft = Draft.objects.create(
                cube=cube,
                pack_count=pack_count,
                cards_per_pack=cards_per_pack,
                player_count=1,
                max_players=max_players,
                active=True,
            )

            DraftPlayer.objects.create(draft=draft, user=user, role="creator")

            # Notify WebSocket group
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "lobbies",
                {
                    "type": "lobby.update",
                    "event": "create",
                    "draft_id": draft.id,
                    "cube_name": cube.name,
                    "creator": user.username,
                },
            )

            # Return the URL for the frontend to redirect to
            return Response(
                {
                    "redirect_url": reverse("draft-lobby", args=[draft.id]),
                    "message": "Lobby created successfully!",
                },
                status=status.HTTP_201_CREATED,
            )

        except Cube.DoesNotExist:
            return Response({"error": "Cube not found"}, status=status.HTTP_400_BAD_REQUEST)
        


    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start_draft(self, request, pk=None):
        draft = self.get_object()
        cube = draft.cube  # Ensure we're referencing the correct cube

        logger.info(f"Starting draft for Cube ID: {cube.id}")  # Log the cube ID

        cube_cards = CubeCard.objects.filter(cube=cube).values_list("card", flat=True)

        if draft.players.count() < 2:
            return Response({"error": "Not enough players to start the draft."}, status=status.HTTP_400_BAD_REQUEST)

        # Count card quantities in the cube
        card_quantities = Counter(cube_cards)

        # Create a list of cards considering their quantities
        all_cards = []
        for card_id, quantity in card_quantities.items():
            all_cards.extend([card_id] * quantity)


        card_names = [Card.objects.get(id=card_id).name for card_id in set(cube_cards)]
        logger.info(f"Cards eligible for the draft: {', '.join(card_names)}")  # Log the card names

        # Shuffle cards to randomize
        shuffle(all_cards)

        try:
            # Create draft packs for each player
            players = draft.players.all()
            num_players = len(players)
            total_packs = draft.pack_count * num_players
            cards_per_pack = draft.cards_per_pack

            if len(all_cards) < total_packs * cards_per_pack:
                return Response({"error": "Not enough cards in the cube to start the draft."}, status=status.HTTP_400_BAD_REQUEST)

            for pack_number in range(total_packs):
                player = players[pack_number % num_players].user
                pack_cards = all_cards[pack_number * cards_per_pack:(pack_number + 1) * cards_per_pack]
                pack = DraftPack.objects.create(draft=draft, player=player)
                pack.cards.set(pack_cards)

                logger.info(f"Pack {pack_number + 1} created for {player.username} with {len(pack_cards)} cards.")

            draft.active = False
            draft.save()

            return Response({"message": "Draft started successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeckListViewSet(viewsets.ModelViewSet):
    queryset = DeckList.objects.all()
    serializer_class = DeckListSerializer


class CubeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        # Required fields
        cube_name = data.get("name")
        card_list = data.get("card_list")

        # Optional fields
        description = data.get("description", "")
        power_level = data.get("power_level", "")
        tags = data.get("tags", "")

        if not cube_name or not card_list:
            return Response(
                {"error": "Cube name and card list are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create Cube
        cube = Cube.objects.create(
            name=cube_name,
            creator=user,
            description=description,
            power_level=power_level,
            tags=tags,
            card_count=len(card_list.splitlines()),  # Count cards
        )

        card_images = []

        # Process cards
        for line in card_list.splitlines():
            try:
                count, name = line.split(" ", 1)
                count = int(count)
                name = name.strip()
            except ValueError:
                continue  # Skip invalid lines

            # Fetch or create the card
            card, _ = Card.objects.get_or_create(
                name=name,
                defaults={"mana_cost": None, "color": None, "type_line": None},
            )

            # Fetch images from existing CardImage model
            images = CardImage.objects.filter(card=card)
            if images.exists():
                card_images.extend(images)

            # Create CubeCard relationship
            CubeCard.objects.create(cube=cube, card=card)

        # Assign a random image from the card images to the Cube
        if card_images:
            chosen_image = random.choice(card_images)
            CubeImage.objects.create(
                cube=cube, image_url=chosen_image.image_url, is_primary=True
            )

        return Response(
            {"message": "Cube uploaded successfully!", "id": cube.id},
            status=status.HTTP_201_CREATED,
        )




class UpdateCardDatabaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger = logging.getLogger(__name__)
        DEFAULT_IMAGE_URL = "https://example.com/default_card_image.jpg"  # Replace with your default image URL

        try:
            # Fetch Scryfall bulk data
            logger.info("Fetching bulk data metadata from Scryfall...")
            metadata_response = requests.get("https://api.scryfall.com/bulk-data")
            metadata_response.raise_for_status()
            bulk_data = metadata_response.json()

            default_cards_data = next(
                item for item in bulk_data["data"] if item["type"] == "default_cards"
            )
            download_url = default_cards_data["download_uri"]

            logger.info("Fetching card data from Scryfall...")
            card_data_response = requests.get(download_url)
            card_data_response.raise_for_status()
            scryfall_data = card_data_response.json()

            # Process card data
            logger.info("Processing card data...")
            for card_data in scryfall_data:
                name = card_data.get("name", "").strip()
                mana_cost = card_data.get("mana_cost", "")
                type_line = card_data.get("type_line", "")
                colors = ",".join(card_data.get("colors", []))
                image_urls = card_data.get("image_uris", {})

                # Update or create the card
                card, _ = Card.objects.update_or_create(
                    name=name,
                    defaults={
                        "mana_cost": mana_cost,
                        "color": colors,
                        "type_line": type_line,
                    },
                )

                # Store images for the card, or assign a default image if none are available
                if image_urls:
                    for size, url in image_urls.items():
                        CardImage.objects.update_or_create(
                            card=card,
                            image_url=url,
                            defaults={"is_primary": size == "normal"},
                        )
                else:
                    # Assign default image
                    CardImage.objects.update_or_create(
                        card=card,
                        image_url=DEFAULT_IMAGE_URL,
                        defaults={"is_primary": True},
                    )

            logger.info("Card database updated successfully!")
            return Response({"message": "Card database updated successfully!"}, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during Scryfall fetch: {e}")
            return Response({"error": f"Network error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception("An error occurred while updating the card database.")
            return Response({"error": f"Failed to update card database: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PopularCubesView(TemplateView):
    template_name = "drafting/popular_cubes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grouped_cubes = {}

        # Iterate through power levels
        for level, level_name in Cube.POWER_LEVEL_CHOICES:
            # Fetch cubes for the current power level
            cubes = Cube.objects.filter(power_level=level).order_by('-draft_count').prefetch_related('images')

            # Create a list of cube data with image handling
            grouped_cubes[level_name] = [
                {
                    "id": cube.id,
                    "name": cube.name,
                    "creator": cube.creator.username,
                    "draft_count": cube.draft_count,
                    "image_url": cube.images.filter(is_primary=True).first().image_url
                    if cube.images.filter(is_primary=True).exists()
                    else "/static/images/default_card.png",  # Fallback image
                }
                for cube in cubes
            ]

        context['grouped_cubes'] = grouped_cubes
        return context


@require_GET
def popular_cubes_api(request):
    # Expecting GET parameters: level (slug) and page (defaults to 2 since first 4 are pre-rendered)
    level_slug = request.GET.get('level')
    try:
        page = int(request.GET.get('page', 2))
    except ValueError:
        page = 2

    # Map the level slug back to the power level code
    power_level_code = None
    for code, label in Cube.POWER_LEVEL_CHOICES:
        if slugify(label) == level_slug:
            power_level_code = code
            break
    if power_level_code is None:
        return JsonResponse({'error': 'Invalid level'}, status=400)

    # Filter cubes by the power level code and order by draft_count descending
    cubes = Cube.objects.filter(power_level=power_level_code).order_by('-draft_count').prefetch_related('images')
    paginator = Paginator(cubes, 4)  # 4 cubes per page

    try:
        cubes_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'cubes': [], 'has_more': False})

    cubes_data = []
    for cube in cubes_page:
        primary_image = cube.images.filter(is_primary=True).first()
        image_url = primary_image.image_url if primary_image else "/static/images/default_card.png"
        cubes_data.append({
            'id': cube.id,
            'name': cube.name,
            'creator': cube.creator.username,
            'draft_count': cube.draft_count,
            'image_url': image_url,
        })

    return JsonResponse({'cubes': cubes_data, 'has_more': cubes_page.has_next()})

class DraftRoomView(TemplateView):
    template_name = "drafting/draft_room.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        draft_id = self.kwargs.get("draft_id")
        draft = Draft.objects.get(id=draft_id)
        players = draft.players.all()  # Use the related_name here
        context['draft'] = draft
        context['players'] = players
        return context



# a_drafting/views.py
class CubeDetailView(DetailView):
    model = Cube
    template_name = "drafting/cube_detail.html"
    context_object_name = "cube"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Cube overview image
        primary_image = self.object.images.filter(is_primary=True).first()
        context['primary_image_url'] = primary_image.image_url if primary_image else "/static/images/default_card.png"
        
        # Build dictionary grouping cards by their color key
        cards_by_color = {}
        for cube_card in self.object.cube_cards.all():
            card = cube_card.card
            # Look up the card's primary image from CardImage
            primary_card_image = card.images.filter(is_primary=True).first() if card.images.filter(is_primary=True).exists() else None
            image_url = primary_card_image.image_url if primary_card_image else "/static/images/default_card.png"
            
            if card.color:
                if ',' in card.color:
                    # For multicolor, split by comma, strip spaces, sort, and rejoin with a slash
                    colors = sorted([col.strip() for col in card.color.split(',')])
                    color_key = '/'.join(colors)
                else:
                    color_key = card.color
            else:
                color_key = "Uncolored"
            
            card_data = {
                'name': card.name,
                'image_url': image_url,
                'color': card.color,
            }
            cards_by_color.setdefault(color_key, []).append(card_data)
        
        # Create an ordered list of (color_key, cards) tuples:
        # Single-color groups first (key does not contain '/') then multicolor groups.
        ordered = sorted(
            cards_by_color.items(),
            key=lambda kv: (1 if '/' in kv[0] else 0, kv[0])
        )
        context['ordered_cards_by_color'] = ordered
        return context