from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class RestaurantProfile(models.Model):
    name = models.CharField(max_length=120, default="Travesía")
    short_description = models.CharField(max_length=220, blank=True)
    long_description = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    google_maps_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    primary_color = models.CharField(max_length=7, default="#9f6b3b")
    hero_title = models.CharField(max_length=120, default="Reserva tu mesa en Travesía")
    hero_subtitle = models.CharField(max_length=220, blank=True)
    logo = models.ImageField(upload_to="restaurant_assets/", blank=True, null=True)
    slot_minutes = models.PositiveIntegerField(default=60, validators=[MinValueValidator(15), MaxValueValidator(240)])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class BusinessHour(models.Model):
    WEEKDAY_CHOICES = [(0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"), (4, "Viernes"), (5, "Sábado"), (6, "Domingo")]
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name="business_hours")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    opens_at = models.TimeField()
    closes_at = models.TimeField()
    is_open = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday", "opens_at"]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.opens_at}-{self.closes_at}"

class RestaurantTable(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name="tables")
    name = models.CharField(max_length=60)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["capacity", "name"]
        unique_together = ("restaurant", "name")

    def __str__(self):
        return f"{self.name} ({self.capacity} pax)"

class BlockedDate(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name="blocked_dates")
    date = models.DateField()
    reason = models.CharField(max_length=180, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["date"]
        unique_together = ("restaurant", "date")

class BlockedTimeSlot(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name="blocked_slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=180, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["date", "start_time"]
