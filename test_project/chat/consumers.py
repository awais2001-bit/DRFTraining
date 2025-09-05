import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from django.contrib.auth import get_user_model
from .tasks import send_email_notification

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"] #scope works like request in django views
        if not user or user.is_anonymous:
            await self.close()
            return
        self.user = user
        self.room_name = self.scoe['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        
        #join group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        
        #implementing session, as session are not automatically saved in websocket
        session = self.scope['session']
        if session is not None:
            if session.get('msg_count') is None:
                session['msg_count'] = 0
                
                await database_sync_to_async(session.save)() # Save the session asynchronously to the database, as database ORM is synchronus so this method is used
                
        await self.accept()
        
        
async def disconnect(self, close_code):
    
    await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    

async def receive(self, text_data=None, bytes_data=None):
    if text_data is None:
        return 
    
    data = json.loads(text_data)
    message = data.get("message", "").strip()
    
    session = self.scope['session']
    if session is not None:
        session['msg_count'] = session.get('msg_count', 0) + 1
        await database_sync_to_async(session.save)()
        
        
    await self.save_message(self.user.id, self.room_name, message)
    
    #broadcast message to group
    
    event = {
        "type": "chat.message",
        "message": message,
        "username": self.user.username,
        'room_name': self.room_name,
        'msg_count': session.get('msg_count', 0)
    }
    
    await self.channel_layer.group_send(self.room_group_name, event)
    
    #usig celery to send email notification
    try:
     await send_email_notification.delay(self.user.email, self.room_name, message)
    except Exception as e:
        print(f"Error sending email notification: {e}")
        
    
async def chat_message(self, event):
    await self.send(text_data=json.dumps({
        "message": event["message"],
        "username": event["username"],
        "room_name": event["room_name"],
        "msg_count": event["msg_count"]
    }))
    
@database_sync_to_async
def save_message(self, user_id, room_name, content):
    user = User.objects.get(id=user_id)
    return Message.objects.create(user=user, room_name=room_name, content=content)
