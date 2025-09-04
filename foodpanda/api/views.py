from api.models import User,Restaurant,MenuItem,Order,OrderItem
from api.serializers import UserSerializer,OrderStatusSerializer,OrderSerializer,MenuItemSerializer,RestaurantSerializer
from rest_framework import viewsets,filters,generics
from rest_framework.permissions import AllowAny,IsAdminUser,IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied,NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.utils.timezone import now
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from api.tasks import send_restaurant_confirmation, send_order_confirmation
from celery.task.control import revoke

# Create your views here.



class UserView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    
    
    
class RestaurantView(viewsets.ModelViewSet):
    serializer_class = RestaurantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'menu_items':
            return MenuItemSerializer
        return RestaurantSerializer
    
    def get_queryset(self):
        user = self.request.user
        query_set = Restaurant.objects.select_related('owner').filter(owner=user)
        return query_set
    
    def perform_create(self,serializer):
        serializer.save(owner=self.request.user)
        restaurant_name = serializer.data['name']
        user_email = self.request.user.email
        send_restaurant_confirmation.delay(restaurant_name,user_email)
    
    @action(detail=True, methods=['get','post','put','delete'], url_path='menu-items', url_name='restaurant-items')
    def menu_items(self,request,pk=None):
        restaurant = self.get_object()
        
        if request.method == 'GET':
            items = restaurant.menu_items.all()
            serializer = MenuItemSerializer(items, many=True)
            return Response(serializer.data)
        
        else:
            if restaurant.owner != request.user:
                return Response(
                    {"error": "You are not allowed to add items to this restaurant."},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            serializer = MenuItemSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(restaurant=restaurant)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
        
    
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "customer":
            return Order.objects.filter(customer=user).select_related('restaurant').prefetch_related('order_items__menu_item')
        elif user.role == "owner":
            return Order.objects.filter(restaurant__owner=user).select_related('customer').prefetch_related('order_items__menu_item')
        return Order.objects.none()

    def perform_create(self, serializer):
        order = serializer.save(customer=self.request.user)
        result = send_order_confirmation.apply_async(args=[serializer.order.id, self.request.user.email],countdown=300, expires=900)
        order.celery_task_id = result.id
        order.save()
        
    @action(detail=True, methods=['patch'], url_path='status', url_name='order-status')
    def update_status(self, request, pk=None):
        order = self.get_object()
        user = request.user

        if order.restaurant.owner != user:
            return Response({"error": "Only restaurant owner can update status"}, status=403)

        serializer = OrderStatusSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        if order.status == Order.Status.CANCELLED and order.celery_task_id:
            revoke(order.celery_task_id, terminate=True) # Invalidate the task
            order.celery_task_id = None
            order.save()
            

        return Response(serializer.data)
    