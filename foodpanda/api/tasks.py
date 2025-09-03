from __future__ import annotations
from celery import shared_task, current_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.conf import settings

from django.utils.timezone import now, timedelta
import csv
import os
from .models import Order, OrderItem, Restaurant, MenuItem
from django.db.models import Count, Q



logger = get_task_logger(__name__)


@shared_task
def send_restaurant_confirmation(restaurant_name, user_email):
    subject = "Restaurant Registration Confirmation"
    message = f"Welcom to FOODPANDA!!\nYour restaurant '{restaurant_name}' has been successfully registered.\n This is system generated email so DONOT REPLY!!"
    sender = 'no-reply@foodpanda.com'
    
    send_mail(subject, message, sender, [user_email])
    return f"Confirmation email sent to {user_email} for {restaurant_name}"


@shared_task(bind=True, max_retries=3)
def send_order_confirmation(self, order_id, user_email):
    try:
        subject = 'Order Confirmation'
        message = f'Your order with ID {order_id} has been successfully placed. Thank you for ordering with FOODPANDA!'
        sender = 'no-reply@foodpanda.com'
        
        send_mail(subject, message, sender, [user_email])
        return f"Order confirmation email sent to {user_email} for order {order_id}"

    except Exception as e:
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def daily_orders_received(self):
    today = now().date()
    end = today + timedelta(days=1)
    
    restaurants = Restaurant.objects.select_related('owner').annotate(
    daily_orders=Count(
        "orders",  
        filter=Q(order__created_at__gte=today, order__created_at__lt=end)
    )
)
    
    for restaurant in restaurants:
        subject = f"Daily Order Summary - {restaurant.name}"
        message = (
                f"Hello {restaurant.owner.username},\n\n"
                f"Today you received {restaurant.daily_orders} orders "
                f"at your restaurant '{restaurant.name}'.\n\n"
                "Thank you for using Foodpanda!"
            )
        sender = 'noreply@foodpanda.com'
        recipient = [restaurant.owner.email]
        
        send_mail(subject, message, sender, recipient)
        
    return f"Daily order summaries sent to {restaurants.count()} restaurants."


        