from django import forms
from .models import RestaurantProfile, BlockedDate, BlockedTimeSlot, BusinessHour, RestaurantTable

class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = RestaurantProfile
        fields = [
            "name","short_description","long_description","phone","email","address",
            "google_maps_url","whatsapp_number","primary_color","hero_title",
            "hero_subtitle","logo","slot_minutes","is_active"
        ]
        widgets = {"long_description": forms.Textarea(attrs={"rows": 4})}

class RestaurantTableForm(forms.ModelForm):
    class Meta:
        model = RestaurantTable
        fields = ["name", "capacity", "is_active"]

class BlockedDateForm(forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ["date","reason","is_active"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

class BlockedTimeSlotForm(forms.ModelForm):
    class Meta:
        model = BlockedTimeSlot
        fields = ["date","start_time","end_time","reason","is_active"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

class BusinessHourForm(forms.ModelForm):
    class Meta:
        model = BusinessHour
        fields = ["weekday","opens_at","closes_at","is_open"]
        widgets = {
            "opens_at": forms.TimeInput(attrs={"type": "time"}),
            "closes_at": forms.TimeInput(attrs={"type": "time"}),
        }
