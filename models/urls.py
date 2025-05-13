from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarViewSet, ParkingZoneViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'cars', CarViewSet)
router.register(r'parking-zones', ParkingZoneViewSet)
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path
from .views import RegisterView, LoginView, LogoutView, ChangePasswordView, ResetPasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]