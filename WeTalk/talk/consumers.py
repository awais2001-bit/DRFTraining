import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, ActiveConnection
from django.db import models
from django.utils import timezone

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        self.other_username = self.scope["url_route"]["kwargs"]["username"]
        self.other_user = await self.get_user(self.other_username)
        if not self.other_user:
            await self.close()
            return

       

        # Get or create chatroom
        self.chatroom = await self.get_or_create_room(self.user, self.other_user)
        self.room_group_name = f"chat_{self.chatroom.id}"

        # Add to the group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.add_active_connection(self.user, self.room_group_name)

        await self.accept()

        # Send past messages
        past_messages = await self.get_past_messages(self.chatroom.id)
        for msg in past_messages:
            await self.send(text_data=json.dumps({
                "sender": msg["sender__username"],
                "message": msg["text"],
                "timestamp": msg["time_stamp"].isoformat(),
            }))
        
        

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            if not message:
                return

            # Save message
            msg_obj = await self.save_message(self.user.id, self.chatroom.id, message)
            await self.update_connection_activity(self.user, self.room_group_name)


            # Broadcast message to room
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "chat.message",
                "sender": self.user.username,
                "message": msg_obj.text,
                "timestamp": msg_obj.time_stamp.isoformat(),
            })

            # Broadcast notification
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "chat.notification",
                "sender": self.user.username,
                "notification": f"New message from {self.user.username}",
                "chat_room": self.chatroom.id,
            })

        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "message": event["message"],
            "timestamp": event["timestamp"],
        }))

    async def chat_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "sender": event["sender"],
            "notification": event["notification"],
            "chat_room": event["chat_room"],
        }))

    @database_sync_to_async
    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, user_id, room_id, content):
        user = User.objects.get(id=user_id)
        room = ChatRoom.objects.get(id=room_id)
        return Message.objects.create(sender=user, chat_room=room, text=content)

    @database_sync_to_async
    def get_or_create_room(self, user1, user2):
        # Enforce consistent order to avoid duplicate rooms
        if user1.id > user2.id:
            user1, user2 = user2, user1
        room, created = ChatRoom.objects.get_or_create(user1=user1, user2=user2)
        return room

    @database_sync_to_async
    def get_past_messages(self, room_id):
        return list(
            Message.objects.filter(chat_room_id=room_id)
            .select_related("sender")
            .values("sender__username", "text", "time_stamp")
            .order_by("time_stamp")
        )

    @database_sync_to_async
    def add_active_connection(user, room_name):
        obj, created = ActiveConnection.objects.update_or_create(
            user=user,
            room_name=room_name,
            defaults={"last_active": timezone.now()},
        )
        return obj
    
    @database_sync_to_async
    def update_connection_activity(user, room_name):
        ActiveConnection.objects.filter(user=user, room_name=room_name).update(last_active=timezone.now())