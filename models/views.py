from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Car, ParkingZone, Booking
from .serializers import CarSerializer, ParkingZoneSerializer, BookingSerializer
from datetime import datetime

class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ParkingZoneViewSet(viewsets.ModelViewSet):
    queryset = ParkingZone.objects.all()
    serializer_class = ParkingZoneSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data
        data['start_time'] = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        data['end_time'] = data['start_time'] + timedelta(hours=1)

        parking_zone = ParkingZone.objects.get(id=data['parking_zone']['id'])

        if parking_zone.available_spots <= 0:
            return Response({'error': 'No available spots'}, status=status.HTTP_400_BAD_REQUEST)

        booking = Booking(user=request.user, parking_zone=parking_zone, **data)
        booking.save()

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
    



from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .serializers import UserSerializer, ProfileSerializer
from .models import Profile
from rest_framework.permissions import IsAuthenticated
from django.utils.crypto import get_random_string
from twilio.rest import Client

TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # SMS verification
        verification_code = get_random_string(length=6, allowed_chars='0123456789')
        profile = Profile.objects.get(user=user)
        profile.phone_number = request.data.get('phone_number')
        profile.save()
        
        client.messages.create(
            body=f"Your verification code is: {verification_code}",
            from_=TWILIO_PHONE_NUMBER,
            to=profile.phone_number
        )

        return Response({"message": "User created. Verify your phone number."}, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"message": "Logged in successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(generics.GenericAPIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)