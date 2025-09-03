from rest_framework.routers import DefaultRouter
from api import views

urlpatterns = [
    
]

router = DefaultRouter()
router.register('user',views.UserView,basename='users')
router.register('restaurants',views.RestaurantView,basename='restaurants')
router.register('order',views.OrderViewSet,basename='orders')



urlpatterns += router.urls
