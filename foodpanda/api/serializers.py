from rest_framework import serializers
from api.models import User, Restaurant, MenuItem, Order, OrderItem
from django.contrib.auth.hashers import make_password


# ---------------------------
#  USER SERIALIZER
# ---------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return make_password(value)   # ✅ hashes the password

    def create(self, validated_data):
        return User.objects.create(**validated_data)


# ---------------------------
#  RESTAURANT SERIALIZER
# ---------------------------
class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ('id', 'name', 'owner')
        read_only_fields = ['owner']

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.is_owner():
            raise serializers.ValidationError("Only owners can create restaurants")
        return attrs

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


# ---------------------------
#  MENU ITEM SERIALIZER
# ---------------------------
class MenuItemSerializer(serializers.ModelSerializer):
    restaurant = serializers.CharField(source='restaurant.name', read_only=True)
    class Meta:
        model = MenuItem
        fields = ('id','restaurant', 'name', 'price', 'available', 'stock')

    def validate(self, attrs):
        if attrs['price'] <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        if attrs['stock'] < 0:
            raise serializers.ValidationError("Stock cannot be negative")

        # ✅ Ensure stock matches availability
        if attrs['available'] and attrs['stock'] == 0:
            raise serializers.ValidationError("Item marked available but stock is 0")
        return attrs


# ---------------------------
#  ORDER ITEM SERIALIZER
# ---------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('menu_item', 'quantity')

    def validate(self, attrs):
        menu_item = attrs['menu_item']
        quantity = attrs['quantity']

        if quantity <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")

        # ✅ Stock check
        if menu_item.stock < quantity:
            raise serializers.ValidationError(
                f"Not enough stock for {menu_item.name}. Available: {menu_item.stock}"
            )

        # ✅ Availability check
        if not menu_item.available:
            raise serializers.ValidationError(f"{menu_item.name} is not available right now")

        return attrs


# ---------------------------
#  ORDER SERIALIZER
# ---------------------------
class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'customer', 'restaurant', 'status', 'order_items', 'total_cost')
        read_only_fields = ['customer', 'status']

    def validate(self, attrs):
        user = self.context['request'].user

        # ✅ Ensure only customers can place orders
        if not user.is_customer():
            raise serializers.ValidationError("Only customers can place orders")

        return attrs

    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items')
        user = self.context['request'].user

        # ✅ Attach logged-in user as customer
        validated_data['customer'] = user
        order = Order.objects.create(**validated_data)

        # ✅ Add items + stock reduction
        for item_data in order_items_data:
            menu_item = item_data['menu_item']
            quantity = item_data['quantity']

            # Prevent cross-restaurant orders
            if menu_item.restaurant != order.restaurant:
                raise serializers.ValidationError(
                    f"{menu_item.name} does not belong to {order.restaurant.name}"
                )

            OrderItem.objects.create(order=order, **item_data)

            menu_item.stock -= quantity
            menu_item.save()

        return order

    def get_total_cost(self, obj):
        return sum(
            item.menu_item.price * item.quantity
            for item in obj.order_items.all()
        )
        
        
        
class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]  # ✅ only allow updating status

