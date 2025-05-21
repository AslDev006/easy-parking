from django.contrib import admin
from .models import Profile, Car, ParkingZone, Booking

# Profile admin
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'is_verified')
    search_fields = ('user__username', 'phone_number')

# Car admin
class CarAdmin(admin.ModelAdmin):
    list_display = ('user', 'make', 'model', 'plate_number')
    search_fields = ('make', 'model', 'plate_number')
    list_filter = ('user',)

# ParkingZone admin
class ParkingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'total_spots', 'available_spots')
    search_fields = ('name', 'location')

# Booking admin
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'parking_zone', 'car', 'start_time', 'end_time', 'penalty')
    search_fields = ('user__username', 'car__plate_number', 'parking_zone__name')
    list_filter = ('parking_zone', 'user')

# Register models with admin
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Car, CarAdmin)
admin.site.register(ParkingZone, ParkingZoneAdmin)
admin.site.register(Booking, BookingAdmin)