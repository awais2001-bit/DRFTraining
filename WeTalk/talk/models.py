from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# Create your models here.


class User(AbstractUser):
    pass


class Contact(models.Model):
    user = models.ForeignKey(User, related_name='contacts', on_delete=models.CASCADE)
    contact = models.ForeignKey(User, related_name='added_as_contact', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'contact')
    
    def __str__(self):
        return f"{self.display_name or self.contact.username} (saved by {self.user.username})"

        
        
class ChatRoom(models.Model):
    user1 = models.ForeignKey(User, related_name='chatrooms_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chatrooms_user2', on_delete=models.CASCADE)
    
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user1", "user2"],
                name="unique_chatroom_users"
            )
        ]
    
    #used this so no duplicate chatrooms are created between same users
    def save(self, *args, **kwargs):
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"
        
    
        
class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    text = models.TextField()
    time_stamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['time_stamp']
        
    def __str__(self):
        return f"{self.sender.username}: {self.text[:20]}"
    

class ActiveConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255)
    last_active = models.DateTimeField(default=timezone.now)