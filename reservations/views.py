from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.shortcuts import redirect
from .forms import PublicReservationForm
from .services import get_active_restaurant, assign_table_for_reservation

class ReservationCreateView(FormView):
    template_name = "reservations/reservation_form.html"
    form_class = PublicReservationForm
    success_url = reverse_lazy("reservations:success")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["language"] = getattr(self.request, "LANGUAGE_CODE", "es")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["restaurant"] = get_active_restaurant()
        context["current_language"] = getattr(self.request, "LANGUAGE_CODE", "es")
        return context

    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.restaurant = get_active_restaurant()
        assign_table_for_reservation(reservation)
        reservation.save()
        current_language = getattr(self.request, "LANGUAGE_CODE", "es")
        if current_language == "en":
            email_message = (
                f"Hello {reservation.customer_name},\n\n"
                f"We received your reservation request for {reservation.party_size} people on {reservation.reservation_date} at {reservation.reservation_time}.\n"
                "Thank you for booking with us."
            )
            success_message = "Your reservation request was sent successfully."
        else:
            email_message = (
                f"Hola {reservation.customer_name},\n\n"
                f"Recibimos tu solicitud de reserva para {reservation.party_size} personas el {reservation.reservation_date} a las {reservation.reservation_time}.\n"
                "Gracias por reservar con nosotros."
            )
            success_message = "Tu reserva fue enviada correctamente."

        send_mail(
            subject=f"Reserva recibida - {reservation.restaurant.name}",
            message=email_message,
            from_email=None,
            recipient_list=[reservation.email],
            fail_silently=True,
        )
        messages.success(self.request, success_message)
        return super().form_valid(form)

class ReservationSuccessView(TemplateView):
    template_name = "reservations/reservation_success.html"
