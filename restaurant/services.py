from .models import RestaurantProfile

def get_active_restaurant():
    return RestaurantProfile.objects.filter(is_active=True).first()
