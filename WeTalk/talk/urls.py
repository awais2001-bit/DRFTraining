from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ContactViewSet, ChatRoomViewSet, MessageViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("contacts", ContactViewSet, basename="contact")
router.register("chatrooms", ChatRoomViewSet, basename="chatroom")
router.register("messages", MessageViewSet, basename="message")

urlpatterns = [
    path("", include(router.urls)),
]
