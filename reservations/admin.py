from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("customer_name","reservation_date","reservation_time","party_size","status","attended","created_by_staff")
    list_filter = ("status","reservation_date","attended","created_by_staff")
    search_fields = ("customer_name","phone","email")
