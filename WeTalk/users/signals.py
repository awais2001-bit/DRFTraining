from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from talk.models import User
from .tasks import send_welcome_email, send_login_email


@receiver(post_save, sender=User)
def user_created_signal(sender, instance, created, **kwargs):
    if created:  
        send_welcome_email.delay(instance.email, instance.username)


@receiver(user_logged_in)
def user_login_signal(sender, request, user, **kwargs):
    send_login_email.delay(user.email, user.username)
