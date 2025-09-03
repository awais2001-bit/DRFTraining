# tests.py

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Restaurant, MenuItem, Order, OrderItem

from django.contrib.auth import get_user_model



User = get_user_model()
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class FoodPandaAPITests(APITestCase):

    def setUp(self):
        # Create users
        self.owner = User.objects.create_user(username="owner", password="pass123")
        self.customer = User.objects.create_user(username="customer", password="pass123")

        # Generate JWT tokens
        self.owner_token = get_tokens_for_user(self.owner)['access']
        self.customer_token = get_tokens_for_user(self.customer)['access']

        # Create restaurant for owner
        self.restaurant = Restaurant.objects.create(name="Burger Hub", owner=self.owner)

        # Create menu item
        self.menu_item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Cheese Burger",
            price=250,
            stock=10
        )

    def auth_headers(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # ---------------------- Restaurant Tests ----------------------
    def test_owner_can_create_restaurant(self):
        data = {"name": "Pizza Place"}
        response = self.client.post(
            "/api/restaurants/",
            data,
            **self.auth_headers(self.owner_token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_customer_cannot_create_restaurant(self):
        data = {"name": "Fake Restaurant"}
        response = self.client.post(
            "/api/restaurants/",
            data,
            **self.auth_headers(self.customer_token)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------------------- Menu Item Tests ----------------------
    def test_owner_can_add_menu_item(self):
        data = {"name": "Fries", "price": 100, "stock": 20, "restaurant": self.restaurant.id}
        response = self.client.post(
            f"/api/restaurants/{self.restaurant.id}/menu-items/",
            data,
            **self.auth_headers(self.owner_token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_customer_cannot_add_menu_item(self):
        data = {"name": "Unauthorized Item", "price": 200, "stock": 5, "restaurant": self.restaurant.id}
        response = self.client.post(
            f"/api/restaurants/{self.restaurant.id}/menu-items/",
            data,
            **self.auth_headers(self.customer_token)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------------------- Order Tests ----------------------
    def test_customer_can_place_order(self):
        data = {
            "restaurant_id": self.restaurant.id,
            "order_items": [
                {"menu_item": self.menu_item.id, "quantity": 2}
            ]
        }
        response = self.client.post(
            "/api/orders/",
            data,
            format="json",
            **self.auth_headers(self.customer_token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_order_stock_validation(self):
        data = {
            "restaurant_id": self.restaurant.id,
            "order_items": [
                {"menu_item": self.menu_item.id, "quantity": 9999}
            ]
        }
        response = self.client.post(
            "/api/orders/",
            data,
            format="json",
            **self.auth_headers(self.customer_token)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Not enough stock", str(response.data))

    
