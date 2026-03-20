from restaurant.models import RestaurantProfile
def restaurant_context(request):
    return {"site_restaurant": RestaurantProfile.objects.filter(is_active=True).first()}
