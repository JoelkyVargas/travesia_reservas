from django.urls import path
from .views import HomeView, MenuView, ContactView

app_name = "core"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("menu/", MenuView.as_view(), name="menu"),
    path("contacto/", ContactView.as_view(), name="contact"),
]
