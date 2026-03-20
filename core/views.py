from django.views.generic import TemplateView
from restaurant.models import RestaurantProfile

class HomeView(TemplateView):
    template_name = "core/home.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["restaurant"] = RestaurantProfile.objects.filter(is_active=True).first()
        return context

class MenuView(TemplateView):
    template_name = "core/menu.html"

class ContactView(TemplateView):
    template_name = "core/contact.html"
