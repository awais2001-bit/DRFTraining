from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import Contact, ChatRoom, Message
from .serializers import (
    UserSerializer,
    ContactSerializer,
    ChatRoomSerializer,
    MessageSerializer
)

User = get_user_model()



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  

    def get_permissions(self):
        if self.action == "create":  
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()] 


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user) 



class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(user1=user) | ChatRoom.objects.filter(user2=user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            chat_room__user1=user
        ) | Message.objects.filter(
            chat_room__user2=user
        )

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
