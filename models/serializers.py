from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Car, ParkingZone, Booking
from django.db import transaction  # Atomik tranzaksiyalar uchun


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
        # Agar CarViewSet da perform_create orqali user=self.request.user qilinsa,
        # bu yerdagi 'user' validated_data da bo'lishi yoki ViewSet da o'rnatilishi kerak.
        # Hozirgi holatda, client 'user' ID sini yuborishi kutiladi.
        car = Car.objects.create(**validated_data)
        return car


class ParkingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingZone
        fields = ['id', 'name', 'location', 'total_spots', 'available_spots']


class BookingSerializer(serializers.ModelSerializer):  # Variant 1
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

        # Vaqt validatsiyasi (masalan, start_time end_time dan oldin bo'lishi)
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    {"end_time": "Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."}
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
        new_parking_zone_from_data = validated_data.get('parking_zone', old_parking_zone)

        parking_zone_changed = (old_parking_zone != new_parking_zone_from_data)

        if parking_zone_changed:
            if new_parking_zone_from_data.available_spots <= 0:
                raise serializers.ValidationError(
                    {"parking_zone": f"Yangi tanlangan joyda ({new_parking_zone_from_data.name}) bo'sh o'rin yo'q."}
                )

        updated_instance = super().update(instance, validated_data)

        if parking_zone_changed:
            with transaction.atomic():
                old_parking_zone.available_spots += 1
                old_parking_zone.save(update_fields=['available_spots'])

                new_parking_zone_from_data.available_spots -= 1
                new_parking_zone_from_data.save(update_fields=['available_spots'])

        return updated_instance


class BookingNestedWriteSerializer(serializers.ModelSerializer):  # Variant 2
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    car = CarSerializer()
    parking_zone = serializers.PrimaryKeyRelatedField(queryset=ParkingZone.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'parking_zone', 'start_time', 'end_time', 'penalty']
        read_only_fields = ['penalty']

    def create(self, validated_data):
        car_data = validated_data.pop('car')
        current_user = validated_data.get('user')  # Bu user ViewSet da o'rnatilishi kerak yoki client yuborishi kerak

        # Car uchun user ni o'rnatish
        # Agar CarSerializer da 'user' maydoni bo'lsa va u yoziladigan bo'lsa, car_data da 'user' bo'lishi kerak.
        # Agar CarSerializer da 'user' HiddenField(default=CurrentUserDefault) bo'lsa, u avtomatik olinadi.
        # Hozirgi CarSerializer PrimaryKeyRelatedField ishlatadi, shuning uchun car_data['user'] ni o'rnatish kerak.
        car_data_user_id = car_data.get('user')
        if isinstance(car_data_user_id, User):  # Agar CarSerializer dan User obyekti kelsa
            car_data['user'] = car_data_user_id
        elif car_data_user_id is None:  # Agar CarSerializer da user yuborilmasa, booking userini ishlatamiz
            car_data['user'] = current_user

        # Car ni olish yoki yaratish
        # Bu logikani aniqlashtirish kerak: har doim yangi car yaratiladimi yoki mavjudini ishlatadimi?
        # Agar plate_number va user bilan unikal bo'lsa:
        car_instance, created = Car.objects.get_or_create(
            user=car_data['user'],  # Yoki car_data['user'].id agar u obyekt bo'lsa
            plate_number=car_data['plate_number'],
            defaults={'make': car_data['make'], 'model': car_data['model']}
        )

        parking_zone_instance = validated_data.get('parking_zone')

        if parking_zone_instance.available_spots <= 0:
            raise serializers.ValidationError({"parking_zone": "Bu joyda bo'sh o'rin yo'q."})

        booking = Booking.objects.create(car=car_instance, parking_zone=parking_zone_instance, user=current_user,
                                         start_time=validated_data['start_time'], end_time=validated_data['end_time'])

        parking_zone_instance.available_spots -= 1
        parking_zone_instance.save(update_fields=['available_spots'])
        return booking


class BookingReadSerializer(serializers.ModelSerializer):  # Variant 3 - O'qish uchun
    user = UserSerializer(read_only=True)
    car = CarSerializer(read_only=True)
    parking_zone = ParkingZoneSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'parking_zone', 'start_time', 'end_time', 'penalty']


class BookingWriteSerializer(serializers.ModelSerializer):  # Variant 3 - Yozish uchun
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    car = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.all(),
    )
    parking_zone = serializers.PrimaryKeyRelatedField(queryset=ParkingZone.objects.all())

    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'parking_zone', 'start_time', 'end_time']  # penalty model.save() da hisoblanadi

    def validate_car(self, car_instance):
        request_user = self.context['request'].user
        if car_instance.user != request_user:
            raise serializers.ValidationError("Siz faqat o'zingizning mashinangizni tanlashingiz mumkin.")
        return car_instance

    def validate_parking_zone(self, parking_zone_instance):
        # Agar update bo'lsa va bu booking shu joyni egallab turgan bo'lsa, available_spots=0 bo'lishi mumkin
        # Lekin yangi joyga o'tayotganda yoki yangi booking yaratayotganda tekshirish kerak
        is_update = self.instance is not None
        if is_update and self.instance.parking_zone == parking_zone_instance:
            # O'z joyida qolayotgan bo'lsa, available_spots ni tekshirish shart emas
            pass
        elif parking_zone_instance.available_spots <= 0:
            raise serializers.ValidationError("Bu joyda bo'sh o'rin yo'q.")
        return parking_zone_instance

    def validate(self, data):
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    {"end_time": "Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."}
                )
        return data

    def create(self, validated_data):
        parking_zone = validated_data.get('parking_zone')
        # validate_parking_zone da tekshirilgan

        booking = Booking.objects.create(**validated_data)

        parking_zone.available_spots -= 1
        parking_zone.save(update_fields=['available_spots'])
        return booking

    def update(self, instance, validated_data):
        old_parking_zone = instance.parking_zone
        new_parking_zone_from_data = validated_data.get('parking_zone', old_parking_zone)

        parking_zone_changed = (old_parking_zone != new_parking_zone_from_data)

        if parking_zone_changed:
            pass

        updated_instance = super().update(instance, validated_data)

        if parking_zone_changed:
            with transaction.atomic():
                old_parking_zone.available_spots += 1
                old_parking_zone.save(update_fields=['available_spots'])

                # updated_instance.parking_zone bu yangi parking zona
                updated_instance.parking_zone.available_spots -= 1
                updated_instance.parking_zone.save(update_fields=['available_spots'])

        return updated_instance