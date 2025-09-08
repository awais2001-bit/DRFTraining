from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_welcome_email(email, username):
    subject = "Welcome to WeTalk!"
    message = f"Hi {username},\n\nThanks for creating an account at WeTalk."
    sender = 'noreply@WeTalk.com'
    send_mail(subject, message, sender, [email])


@shared_task
def send_login_email(email, username):
    subject = "Login Alert"
    message = f"Hi {username},\n\nYou just logged into your WeTalk account."
    sender = 'noreply@WeTalk.com'
    send_mail(subject, message, sender, [email])
