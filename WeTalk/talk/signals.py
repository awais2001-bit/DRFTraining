from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Message

@receiver(post_save, sender=Message)
def message_created_signal(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        room_group = f'chat_{instance.chat_room.id}'
        
        
        async_to_sync(channel_layer.group_send)(
            room_group, {
                "type": "chat.notification",
                "notification": f"New message from {instance.sender.username}",
                "sender": instance.sender.username,
                "chat_room": instance.chat_room.id,
            }
        )