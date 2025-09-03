from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        OWNER = "owner", "Owner"
    email = models.EmailField(unique=True)

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)

    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    def is_owner(self):
        return self.role == self.Role.OWNER


class Restaurant(models.Model):
    name = models.CharField(max_length=60, unique=True)
    owner = models.ForeignKey(User, related_name="restaurants", on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name="menu_items", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be greater than 0.")

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, related_name="orders", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="order_items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name="order_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} (Order {self.order.id})"
