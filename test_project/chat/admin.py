from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room_name", "user", "timestamp")
    list_filter = ("room_name", "timestamp")
    search_fields = ("content", "user__username")
