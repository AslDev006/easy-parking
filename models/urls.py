from django.urls import path
from .views import (
    CarViewSet,
    ParkingZoneViewSet,
    BookingViewSet,
    RegisterView,
    LoginView,
    LogoutView,
    ChangePasswordView,
    ResetPasswordView
)

urlpatterns = [

    path('api/cars/', CarViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='car-list'),

    path('api/cars/<int:pk>/', CarViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='car-detail'),

    path('api/parking-zones/', ParkingZoneViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='parkingzone-list'),

    path('api/parking-zones/<int:pk>/', ParkingZoneViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='parkingzone-detail'),

    path('api/bookings/', BookingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='booking-list'),

    path('api/bookings/<int:pk>/', BookingViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='booking-detail'),

    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]