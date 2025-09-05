from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.index, name="chat_index"),
    path("room/<str:room_name>/", views.room, name="chat_room"),
    path("login/", auth_views.LoginView.as_view(template_name="chat/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
]
