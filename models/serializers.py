from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from .models import Car, ParkingZone, Booking

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'is_verified']


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['id', 'make', 'model', 'plate_number']

class ParkingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingZone
        fields = ['id', 'name', 'location', 'total_spots', 'available_spots']

class BookingSerializer(serializers.ModelSerializer):
    car = CarSerializer()
    parking_zone = ParkingZoneSerializer()

    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'parking_zone', 'start_time', 'end_time', 'penalty']

    def create(self, validated_data):
        car_data = validated_data.pop('car')
        parking_zone_data = validated_data.pop('parking_zone')

        car = Car.objects.create(**car_data)
        parking_zone = ParkingZone.objects.get(id=parking_zone_data['id'])

        booking = Booking.objects.create(car=car, parking_zone=parking_zone, **validated_data)
        parking_zone.available_spots -= 1
        parking_zone.save()

        return booking