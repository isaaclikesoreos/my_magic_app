from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

# Global dictionary to track players in each draft room
draft_rooms = {}


class DraftConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.draft_id = self.scope["url_route"]["kwargs"]["draft_id"]  # Retrieve draft_id from the URL
        self.draft_group_name = f"draft_{self.draft_id}"
        self.user = self.scope["user"]  # Ensure user authentication is configured

        logger.info(f"WebSocket connection attempt for draft {self.draft_id}")

        # Initialize the draft room in the global dictionary if not already present
        if self.draft_id not in draft_rooms:
            draft_rooms[self.draft_id] = []

        # Check if the user is already in the room
        if any(player["id"] == self.user.id for player in draft_rooms[self.draft_id]):
            logger.warning(f"User {self.user.username} is already in draft {self.draft_id}.")
            await self.close()  # Close connection for duplicate
            return

        # Add the user to the draft's player list
        draft_rooms[self.draft_id].append({
            "id": self.user.id,
            "username": self.user.username,
        })

        # Join the draft group
        await self.channel_layer.group_add(
            self.draft_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connection established for draft {self.draft_id}")

        # Notify the group about the new participant
        await self.channel_layer.group_send(
            self.draft_group_name,
            {
                "type": "draft.update",
                "event": "join",
                "user": {
                    "id": self.user.id,
                    "username": self.user.username,
                },
                "players": draft_rooms[self.draft_id],
                "message": f"{self.user.username} has joined the draft."
            }
        )

        self.ping_task = asyncio.create_task(self.ping_loop())

    async def disconnect(self, close_code):
        # Remove the user from the draft's player list
        if self.draft_id in draft_rooms:
            draft_rooms[self.draft_id] = [
                player for player in draft_rooms[self.draft_id]
                if player["id"] != self.user.id
            ]

            # Clean up empty drafts
            if not draft_rooms[self.draft_id]:
                del draft_rooms[self.draft_id]

        # Notify the group about the disconnection
        await self.channel_layer.group_send(
            self.draft_group_name,
            {
                "type": "draft.update",
                "event": "leave",
                "user": {
                    "id": self.user.id,
                    "username": self.user.username,
                },
                "players": draft_rooms.get(self.draft_id, []),
                "message": f"{self.user.username} has left the draft."
            }
        )

        # Leave the draft group
        await self.channel_layer.group_discard(
            self.draft_group_name,
            self.channel_name
        )

        if hasattr(self, 'ping_task'):
            self.ping_task.cancel()

    # Ping loop for keeping the connection alive
    async def ping_loop(self):
        try:
            while True:
                await self.send(text_data=json.dumps({"type": "ping"}))
                await asyncio.sleep(30)  # Ping every 30 seconds
        except asyncio.CancelledError:
            pass  # Task was cancelled on disconnect

    # Broadcast draft updates to the group
    async def draft_update(self, event):
        await self.send(text_data=json.dumps(event))
