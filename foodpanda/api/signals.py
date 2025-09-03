from django.db.models.signals import post_delete,post_save
from django.dispatch import receiver
from .models import User,Restaurant


@receiver(post_save, sender=Restaurant)
def restaurant_saved(sender, instance, created, **kwargs):
    if created:
        print(f'Restaurant {instance.name} created!')
        
    else:
        print(f'Restaurant {instance.name} updated!')
        
@receiver(post_delete, sender=Restaurant)
def restaurant_deleted(sender, instance, **kwargs):
    print(f'restaurant {instance.name} does not exist anymore!')
    