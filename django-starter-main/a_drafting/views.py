# drafting/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Cube, Card, Draft, CubeCard, DraftPlayer, DeckList, CardImage, CubeImage
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    CubeSerializer, CardSerializer, DraftSerializer, 
    CubeCardSerializer, DraftPlayerSerializer, DeckListSerializer, EmailTokenObtainPairSerializer, CustomUser, CustomUserSerializer, 
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import requests
import logging
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class CubeViewSet(viewsets.ModelViewSet):
    queryset = Cube.objects.all()
    serializer_class = CubeSerializer

    @action(detail=False, methods=['get'], url_path='popular')
    def popular_cubes(self, request):
        popular_cubes = Cube.objects.order_by('-draft_count')[:10]
        serializer = self.get_serializer(popular_cubes, many=True)
        return Response(serializer.data)

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer

class DraftViewSet(viewsets.ModelViewSet):
    queryset = Draft.objects.filter(active=True)
    serializer_class = DraftSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_lobby(self, request):
        user = request.user
        data = request.data

        cube_id = data.get("cube_id")
        pack_count = data.get("pack_count", 3)
        cards_per_pack = data.get("cards_per_pack", 15)

        try:
            cube = Cube.objects.get(id=cube_id)
            draft = Draft.objects.create(
                cube=cube,
                pack_count=pack_count,
                cards_per_pack=cards_per_pack,
                player_count=1,
                active=True,
            )

            DraftPlayer.objects.create(draft=draft, user=user, role="creator")

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

            return Response({"message": "Lobby created successfully!", "draft_id": draft.id}, status=status.HTTP_201_CREATED)

        except Cube.DoesNotExist:
            return Response({"error": "Cube not found"}, status=status.HTTP_400_BAD_REQUEST)


class DeckListViewSet(viewsets.ModelViewSet):
    queryset = DeckList.objects.all()
    serializer_class = DeckListSerializer




class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    
    
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

        # Serialize and return the created cube
        serializer = CubeSerializer(cube)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class UpdateCardDatabaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger = logging.getLogger(__name__)

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

                # Store multiple images for the card
                for size, url in image_urls.items():
                    CardImage.objects.update_or_create(
                        card=card,
                        image_url=url,
                        defaults={"is_primary": size == "normal"},
                    )

            logger.info("Card database updated successfully!")
            return Response({"message": "Card database updated successfully!"}, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during Scryfall fetch: {e}")
            return Response({"error": f"Network error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception("An error occurred while updating the card database.")
            return Response({"error": f"Failed to update card database: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
