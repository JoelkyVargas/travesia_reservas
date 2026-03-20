from django.contrib import admin
from .models import RestaurantProfile, BusinessHour, RestaurantTable, BlockedDate, BlockedTimeSlot

class BusinessHourInline(admin.TabularInline):
    model = BusinessHour
    extra = 1

class RestaurantTableInline(admin.TabularInline):
    model = RestaurantTable
    extra = 1

@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(admin.ModelAdmin):
    list_display = ("name","phone","email","slot_minutes","is_active")
    inlines = [BusinessHourInline, RestaurantTableInline]

admin.site.register(BlockedDate)
admin.site.register(BlockedTimeSlot)
