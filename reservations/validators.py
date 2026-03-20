from datetime import date
from django.core.exceptions import ValidationError

def validate_not_past_day(value):
    if value < date.today():
        raise ValidationError("No puedes reservar en una fecha pasada.")
