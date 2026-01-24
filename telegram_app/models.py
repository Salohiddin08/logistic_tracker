# models.py

from django.db import models
# telegram_app/models.py (qo'shimcha modellar)

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, unique=True)
    telegram_session = models.TextField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.phone}"


class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    is_new_device = models.BooleanField(default=False)
    login_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({'New' if self.is_new_device else 'Known'})"
class TelegramSession(models.Model):
    api_id = models.BigIntegerField()
    api_hash = models.CharField(max_length=255)
    string_session = models.TextField()

    def __str__(self):
        return f"Session {self.id}"


class Channel(models.Model):
    channel_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    is_tracked = models.BooleanField(default=False)  # CharField emas, BooleanField bo'lishi kerak

    def __str__(self):
        return f"{self.title} ({self.channel_id})"


class Message(models.Model):
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE)
    message_id = models.BigIntegerField()
    sender_id = models.BigIntegerField(null=True, blank=True)
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('channel', 'message_id')

    def __str__(self):
        return f"Message {self.message_id} from {self.channel.title}"


class TelegramMessage(models.Model):
    message_id = models.BigIntegerField()
    text = models.TextField()
    date = models.DateTimeField()
    user_id = models.BigIntegerField()
    channel_id = models.BigIntegerField()
    location_uz = models.CharField(max_length=255, null=True, blank=True)
    location_ru = models.CharField(max_length=255, null=True, blank=True)
    location_en = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.channel_id}-{self.message_id}"


# ✅ YANGILANGAN: OneToOne → ForeignKey (bir Message da ko'p Shipment bo'lishi mumkin)
class Shipment(models.Model):
    message = models.ForeignKey(
        'Message', 
        on_delete=models.CASCADE, 
        related_name='shipments'  # 'shipment' emas, 'shipments' (ko'plik)
    )
    origin = models.CharField(max_length=255, null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    cargo_type = models.CharField(max_length=255, null=True, blank=True)
    truck_type = models.CharField(max_length=100, null=True, blank=True)
    payment_type = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=64, null=True, blank=True)
    
    # Qo'shimcha maydonlar
    weight = models.CharField(max_length=50, null=True, blank=True)  # "22 т" yoki "23-23,5 т"
    additional_info = models.TextField(null=True, blank=True)  # "Погрузка Душанба"
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-message__date']

    def __str__(self):
        if self.origin or self.destination:
            return f"{self.origin} → {self.destination} ({self.phone})"
        return f"Shipment for message {self.message.message_id}"