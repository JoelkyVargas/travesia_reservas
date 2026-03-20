from django.db import models
from restaurant.models import RestaurantProfile, RestaurantTable

class Reservation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_NO_SHOW = "no_show"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_CONFIRMED, "Confirmada"),
        (STATUS_CANCELLED, "Cancelada"),
        (STATUS_COMPLETED, "Completada"),
        (STATUS_NO_SHOW, "No-show"),
    ]
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name="reservations")
    assigned_table = models.ForeignKey(RestaurantTable, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations")
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    party_size = models.PositiveIntegerField()
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    attended = models.BooleanField(default=False)
    created_by_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["reservation_date", "reservation_time", "-created_at"]

    def __str__(self):
        return f"{self.customer_name} - {self.reservation_date} {self.reservation_time}"
