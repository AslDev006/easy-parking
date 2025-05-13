from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Car(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    plate_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.make} {self.model} ({self.plate_number})"

class ParkingZone(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    total_spots = models.IntegerField()
    available_spots = models.IntegerField()

    def __str__(self):
        return self.name

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parking_zone = models.ForeignKey(ParkingZone, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    penalty = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.parking_zone.name} ({self.car.plate_number})"

    def save(self, *args, **kwargs):
        if self.start_time < (self.end_time - timedelta(minutes=30)):
            self.penalty = 0
        else:
            self.penalty = 50.0
        super().save(*args, **kwargs)