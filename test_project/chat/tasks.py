from celery import shared_task
import time

@shared_task
def send_email_notification(user_email, room_name, message_text):
    time.sleep(0.5)
    print(f"[Celery] Email notify to {user_email}: [{room_name}] {message_text}")
    return True
