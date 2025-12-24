from django.db import models
from django.utils import timezone
import uuid


class Election(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Party(models.Model):
     name = models.CharField(max_length=100)
     party = models.CharField(max_length=100)
     symbol = models.CharField(max_length=50)
     color = models.CharField(max_length=7, default='#000000')
     constituency = models.CharField(max_length=100)
     description = models.TextField(blank=True)
    


     def __str__(self):
        return f"{self.name} - {self.party}"


class Voter(models.Model):
    voter_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    age = models.PositiveIntegerField()
    address = models.TextField()
    
    polling_station = models.CharField(max_length=100)
    has_voted = models.BooleanField(default=False)
    mobile_number = models.CharField(max_length=15, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    constituency = models.CharField(max_length=100)
    # OTP related fields
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveIntegerField(default=0)
    is_blocked = models.BooleanField(default=False)

    # Security / login
    device_id = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.voter_id})"


class Vote(models.Model):
    voter = models.OneToOneField(Voter, on_delete=models.PROTECT)
    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    receipt_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    time = models.DateTimeField(default=timezone.now)
    voted_at = models.DateTimeField(auto_now_add=True)  # ✅ TIME
    def __str__(self):
        return f"{self.voter} → {self.party}"


