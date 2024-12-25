from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
import json
from .models import Draft, DraftPlayer, DraftPack
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


    def start_draft(self, event):
        logger.info(f"Handling 'start_draft' for user: {self.user.username}")

        draft_id = event.get("draft_id")
        if not draft_id:
            logger.error("Draft ID is missing in the WebSocket event.")
            self.send(text_data=json.dumps({"error": "Draft ID is missing."}))
            return

        draft = get_object_or_404(Draft, id=draft_id)
        logger.info(f"Draft found for WebSocket event: {draft}")

        # Get the packs for the player
        packs = DraftPack.objects.filter(draft=draft, player=self.user, is_draft_complete=False)
        if not packs.exists():
            logger.warning(f"No packs found for user: {self.user.username}")
            self.send(text_data=json.dumps({"error": "No draft packs available for you."}))
            return

        pack = packs.first()
        cards = pack.cards.all()
        logger.info(f"Sending pack to user {self.user.username}: {[card.name for card in cards]}")

        card_data = [
            {"name": card.name, "image_url": card.images.filter(is_primary=True).first().image_url or ""}
            for card in cards
        ]

        self.send(text_data=json.dumps({
            "type": "draft.pack",
            "cards": card_data,
        }))
        logger.info(f"WebSocket message sent to user {self.user.username} with pack details.")