from datetime import time
from django.core.management.base import BaseCommand
from restaurant.models import RestaurantProfile, BusinessHour, RestaurantTable

class Command(BaseCommand):
    help = "Carga datos iniciales"

    def handle(self, *args, **options):
        restaurant, _ = RestaurantProfile.objects.get_or_create(
            name="Travesía",
            defaults={
                "short_description": "Cocina contemporánea en La Fortuna.",
                "long_description": "Travesía ofrece una experiencia gastronómica cálida y lista para reservar en línea.",
                "phone": "+506 8888 8888",
                "email": "reservas@travesia.com",
                "address": "La Fortuna, San Carlos, Costa Rica",
                "google_maps_url": "https://maps.google.com",
                "whatsapp_number": "+50688888888",
                "primary_color": "#9f6b3b",
                "hero_title": "Reserva tu mesa en Travesía",
                "hero_subtitle": "Una experiencia gastronómica para disfrutar en La Fortuna.",
                "slot_minutes": 60,
                "reservation_duration_minutes": 120,
                "is_active": True,
            }
        )
        if not restaurant.business_hours.exists():
            schedule = {
                0: ("12:00", "21:00"),
                1: ("12:00", "21:00"),
                2: ("12:00", "21:00"),
                3: ("12:00", "21:00"),
                4: ("12:00", "22:00"),
                5: ("12:00", "22:00"),
                6: ("12:00", "21:00"),
            }
            for weekday, (opens, closes) in schedule.items():
                oh, om = map(int, opens.split(":"))
                ch, cm = map(int, closes.split(":"))
                BusinessHour.objects.get_or_create(
                    restaurant=restaurant,
                    weekday=weekday,
                    opens_at=time(oh, om),
                    closes_at=time(ch, cm),
                    defaults={"is_open": True},
                )
        if not restaurant.tables.exists():
            defaults = [("Mesa 1", 2), ("Mesa 2", 2), ("Mesa 3", 4), ("Mesa 4", 4), ("Mesa 5", 6)]
            for name, capacity in defaults:
                RestaurantTable.objects.get_or_create(
                    restaurant=restaurant, name=name,
                    defaults={"capacity": capacity, "is_active": True}
                )
        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados."))
