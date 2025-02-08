from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
import json
from .models import Draft, DraftPlayer, DraftPack, DraftDeck
import logging

logger = logging.getLogger(__name__)
class DraftConsumer(WebsocketConsumer):
    def connect(self):
        self.draft_id = self.scope["url_route"]["kwargs"]["draft_id"]
        self.draft_group_name = f"draft_{self.draft_id}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            self.close()
            return

        draft = get_object_or_404(Draft, id=self.draft_id)
        DraftPlayer.objects.get_or_create(draft=draft, user=self.user)

        async_to_sync(self.channel_layer.group_add)(
            self.draft_group_name, self.channel_name
        )

        self.accept()
        self.send_player_update()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.draft_group_name, self.channel_name
        )

        draft = get_object_or_404(Draft, id=self.draft_id)
        DraftPlayer.objects.filter(draft=draft, user=self.user).delete()

        self.send_player_update()

    def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("type")

        if event_type == "draft.card":
            self.handle_card_draft(data)
        elif event_type == "start.draft":
            self.start_draft(data)

    def send_player_update(self):
        draft = get_object_or_404(Draft, id=self.draft_id)
        players = draft.players.values("user__username")
        player_data = [{"username": player["user__username"]} for player in players]

        async_to_sync(self.channel_layer.group_send)(
            self.draft_group_name,
            {
                "type": "player.update",
                "players": player_data,
            }
        )

    def player_update(self, event):
        self.send(text_data=json.dumps(event))

    def start_draft(self, data):
        logger.info(f"Handling 'start_draft' for user: {self.user.username}")

        draft_id = data.get("draft_id")
        if not draft_id:
            logger.error("Draft ID is missing in the WebSocket event.")
            self.send(text_data=json.dumps({"error": "Draft ID is missing."}))
            return

        draft = get_object_or_404(Draft, id=draft_id)
        logger.info(f"Draft found for WebSocket event: {draft}")

        # Get all players in the draft
        players = draft.players.all()

        for player in players:
            user = player.user
            packs = DraftPack.objects.filter(draft=draft, player=user, is_draft_complete=False)

            if not packs.exists():
                logger.warning(f"No packs found for user: {user.username}")
                continue  # Skip to the next player if no packs are available

            pack = packs.first()
            cards = pack.cards.all()
            logger.info(f"Sending pack to user {user.username}: {[card.name for card in cards]}")

            card_data = [
                {
                    "name": card.name,
                    "image_url": (card.images.filter(is_primary=True).first().image_url if card.images.filter(is_primary=True).first() else ""),
                }
                for card in cards
            ]

            # Send pack data to the player's WebSocket
            async_to_sync(self.channel_layer.group_send)(
                f"draft_{draft.id}",  # Group name for the draft
                {
                    "type": "draft.pack",
                    "user_id": user.id,  # Include the user ID for targeted front-end handling
                    "cards": card_data,
                }
            )

        logger.info("Draft started, packs sent to all players.")



    def draft_pack(self, event):
        """
        Handle draft.pack event and send data to the front-end.
        """
        user_id = event.get("user_id")
        if self.user.id == user_id:  # Only send to the intended user
            self.send(text_data=json.dumps({
                "type": "draft.pack",
                "cards": event.get("cards"),
            }))


    def handle_card_draft(self, data):
        card_name = data.get("card")
        if not card_name:
            self.send(text_data=json.dumps({"error": "Card name is missing."}))
            return

        draft = get_object_or_404(Draft, id=self.draft_id)
        pack = DraftPack.objects.filter(draft=draft, player=self.user, is_draft_complete=False).first()

        if not pack:
            self.send(text_data=json.dumps({"error": "No active pack found for this player."}))
            return

        # Remove the selected card from the pack and add it to the player's deck
        card = pack.cards.filter(name=card_name).first()
        if not card:
            self.send(text_data=json.dumps({"error": f"Card '{card_name}' not found in the pack."}))
            return

        DraftDeck.objects.create(draft=draft, player=self.user, card=card, mainboard=True)
        pack.cards.remove(card)

        logger.info(f"Player {self.user.username} drafted card: {card_name}")

        # Mark the pack as complete if it becomes empty
        if not pack.cards.exists():
            pack.is_draft_complete = True
            pack.save()

        # Increment the active players counter
        draft.players_with_active_packs += 1
        draft.save()

        # Update the progress of the draft
        self.check_draft_progress(draft)


    def check_draft_progress(self, draft):
        active_packs = DraftPack.objects.filter(draft=draft, is_draft_complete=False)
        total_players = draft.players.count()

        # Log the current draft state
        logger.info(f"Total players: {total_players}")
        logger.info(f"Active packs: {len(active_packs)}")
        logger.info(f"Players who have drafted in this round: {draft.players_with_active_packs}/{total_players}")

        # Rotate packs if all players have drafted
        if draft.players_with_active_packs >= total_players:
            logger.info("All players have drafted. Rotating packs.")
            self.rotate_packs(draft)
        else:
            remaining = total_players - draft.players_with_active_packs
            logger.info(f"Waiting for {remaining} player(s) to make their selection.")

        # End the draft if no active packs remain
        if not active_packs.exists():
            logger.info("No active packs remain. Ending draft.")
            self.end_draft(draft)


    def rotate_packs(self, draft):
        """
        Rotate the packs among players and send new packs if available.
        """
        active_packs = DraftPack.objects.filter(draft=draft, is_draft_complete=False)
        players = list(DraftPlayer.objects.filter(draft=draft).select_related('user'))
        users = [player.user for player in players]  # Extract user objects

        if not active_packs.exists():
            # End draft if no packs are left
            logger.info("No packs left to rotate. Ending draft.")
            self.end_draft(draft)
            self.complete_draft()
            return

        logger.info("Rotating packs among players.")
        # Rotate packs among players
        for pack in active_packs:
            try:
                current_player_index = users.index(pack.player)
                next_player = players[(current_player_index + 1) % len(players)]
                logger.info(f"Pack rotated from {pack.player.username} to {next_player.user.username}")
                pack.player = next_player.user  # Update to the next player
                pack.save()
            except ValueError as e:
                logger.error(f"Error rotating pack: {e}")
                continue  # Skip this pack if there is an issue

        # Reset the player tracking variable
        draft.players_with_active_packs = 0
        draft.save()

        # Notify players of their new packs
        default_image_url = "/static/images/default_card.png"  # Adjust this path as necessary
        for player in players:
            pack = DraftPack.objects.filter(draft=draft, player=player.user, is_draft_complete=False).first()
            if pack:
                cards = pack.cards.all()
                card_data = [
                    {
                        "name": card.name,
                        "image_url": card.images.filter(is_primary=True).first().image_url if card.images.filter(is_primary=True).first() else default_image_url,
                    }
                    for card in cards
                ]
                async_to_sync(self.channel_layer.group_send)(
                    self.draft_group_name,
                    {
                        "type": "draft.pack",
                        "user_id": player.user.id,
                        "cards": card_data,
                    },
                )





    def end_draft(self, draft):
        """
        End the draft and notify all players.
        """
        async_to_sync(self.channel_layer.group_send)(
            self.draft_group_name,
            {
                "type": "draft.complete",
                "message": "Draft is complete. You can view your drafted cards in the results section.",
            },
        )




    def waiting(self, event):
        """
        Handle 'waiting' message type and send it to users who should wait.
        """
        message = event.get("message", "Waiting for all users to make their selection.")
        user_id = event.get("user_id")

        # Only send the message to the intended user
        if self.user.id == user_id:
            self.send(text_data=json.dumps({
                "type": "waiting",
                "message": message
            }))
            

    def complete_draft(self):
        draft = get_object_or_404(Draft, id=self.draft_id)

        # Get all players in the draft
        players = DraftPlayer.objects.filter(draft=draft).select_related("user")
        default_image_url = "/static/images/default_card.png"

        for player in players:
            user = player.user
            drafted_cards = DraftDeck.objects.filter(draft=draft, player=user).select_related("card")
            card_data = [
                {
                    "name": card.card.name,
                    "mana_cost": card.card.mana_cost,  # if you still want it
                    "cmc": card.card.cmc,             # include the numeric CMC value
                    "color": card.card.color,         # optionally include other fields
                    "image_url": (
                        card.card.images.filter(is_primary=True).first().image_url
                        if card.card.images.filter(is_primary=True).exists()
                        else default_image_url
                    ),
                }
                for card in drafted_cards
            ]

            # Send drafted cards only to the specific player's WebSocket
            async_to_sync(self.channel_layer.group_send)(
                self.draft_group_name,
                {
                    "type": "draft.complete",
                    "user_id": user.id,  # Send the user ID for identification
                    "cards": card_data,
                },
            )

        logger.info("Draft completion data sent to all players.")


    def draft_complete(self, event):
        """
        Handle the 'draft.complete' event and ensure the correct player receives their cards.
        """
        user_id = event.get("user_id")
        if self.user.id == user_id:  # Only send to the intended user
            self.send(text_data=json.dumps({
                "type": "draft.complete",
                "cards": event.get("cards", []),  # Send only this player's cards
            }))
