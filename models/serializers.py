from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Car, ParkingZone, Booking

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'phone_number', 'is_verified']

class CarSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=False)

    class Meta:
        model = Car
        fields = ['id', 'user', 'make', 'model', 'plate_number']

    def create(self, validated_data):
        car = Car.objects.create(**validated_data)
        return car

class ParkingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingZone
        fields = ['id', 'name', 'location', 'total_spots', 'available_spots']


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    car = serializers.PrimaryKeyRelatedField(queryset=Car.objects.all())
    parking_zone = serializers.PrimaryKeyRelatedField(queryset=ParkingZone.objects.all())

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'car',
            'parking_zone',
            'start_time',
            'end_time',
            'penalty'
        ]
        read_only_fields = ['penalty']

    def validate(self, data):
        if 'user' in data and 'car' in data:
            if data['car'].user != data['user']:
                raise serializers.ValidationError(
                    {"car": "Bu mashina tanlangan foydalanuvchiga tegishli emas."}
                )
        return data

    def create(self, validated_data):
        parking_zone = validated_data.get('parking_zone')
        if parking_zone.available_spots <= 0:
            raise serializers.ValidationError({"parking_zone": "Bu joyda bo'sh o'rin yo'q."})

        booking = Booking.objects.create(**validated_data)
        parking_zone.available_spots -= 1
        parking_zone.save(update_fields=['available_spots'])
        return booking

    def update(self, instance, validated_data):
        old_parking_zone = instance.parking_zone
        new_parking_zone = validated_data.get('parking_zone', old_parking_zone)

        if old_parking_zone != new_parking_zone:
            if new_parking_zone.available_spots <= 0:
                raise serializers.ValidationError({"parking_zone": "Bu yangi joyda bo'sh o'rin yo'q."})
            old_parking_zone.available_spots += 1
            old_parking_zone.save(update_fields=['available_spots'])
            new_parking_zone.available_spots -= 1
            new_parking_zone.save(update_fields=['available_spots'])

        return super().update(instance, validated_data)


class BookingNestedWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    car = CarSerializer()
    parking_zone = serializers.PrimaryKeyRelatedField(queryset=ParkingZone.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'parking_zone', 'start_time', 'end_time', 'penalty']
        read_only_fields = ['penalty']

    def create(self, validated_data):
        car_data = validated_data.pop('car')
        current_user = validated_data.get('user')
        car_data['user'] = current_user

        car, created = Car.objects.get_or_create(
            user=current_user,
            plate_number=car_data['plate_number'],
            defaults={'make': car_data['make'], 'model': car_data['model']}
        )

        parking_zone = validated_data.get('parking_zone')

        if parking_zone.available_spots <= 0:
            raise serializers.ValidationError({"parking_zone": "Bu joyda bo'sh o'rin yo'q."})

        booking = Booking.objects.create(car=car, **validated_data)
        parking_zone.available_spots -= 1
        parking_zone.save(update_fields=['available_spots'])
        return booking


class BookingReadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    car = CarSerializer(read_only=True)
    parking_zone = ParkingZoneSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'parking_zone', 'start_time', 'end_time', 'penalty']


class BookingWriteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    car = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.all(),
    )
    parking_zone = serializers.PrimaryKeyRelatedField(queryset=ParkingZone.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'parking_zone', 'start_time', 'end_time']

    def validate_car(self, car_instance):
        request_user = self.context['request'].user
        if car_instance.user != request_user:
            raise serializers.ValidationError("Siz faqat o'zingizning mashinangizni tanlashingiz mumkin.")
        return car_instance

    def validate_parking_zone(self, parking_zone_instance):
        if parking_zone_instance.available_spots <= 0:
            if not self.instance:
                 raise serializers.ValidationError("Bu joyda bo'sh o'rin yo'q.")
        return parking_zone_instance

    def create(self, validated_data):
        parking_zone = validated_data.get('parking_zone')
        booking = Booking.objects.create(**validated_data)
        parking_zone.available_spots -= 1
        parking_zone.save(update_fields=['available_spots'])
        return booking

    def update(self, instance, validated_data):
        old_parking_zone = instance.parking_zone
        new_parking_zone = validated_data.get('parking_zone', old_parking_zone)

        instance = super().update(instance, validated_data)

        if old_parking_zone != new_parking_zone:
            if new_parking_zone.available_spots <= 0 and instance.parking_zone == new_parking_zone:
                 pass
            old_parking_zone.available_spots += 1
            old_parking_zone.save(update_fields=['available_spots'])
            new_parking_zone.available_spots -= 1
            new_parking_zone.save(update_fields=['available_spots'])

        return instance