from django.urls import path
from .views import ReservationCreateView, ReservationSuccessView

app_name = "reservations"
urlpatterns = [
    path("reservar/", ReservationCreateView.as_view(), name="create"),
    path("reservar/exito/", ReservationSuccessView.as_view(), name="success"),
]
