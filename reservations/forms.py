from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError
from restaurant.models import RestaurantTable
from .models import Reservation
from .validators import validate_not_past_day
from .services import get_active_restaurant, validate_reservation


class FifteenMinuteTimeField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        super().__init__(*args, choices=choices, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        try:
            return datetime.strptime(value, "%H:%M").time()
        except ValueError as exc:
            raise ValidationError("Selecciona una hora válida.") from exc


class BaseReservationForm(forms.ModelForm):
    reservation_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        validators=[validate_not_past_day],
        label="Fecha",
    )
    reservation_time = FifteenMinuteTimeField(label="Hora")

    class Meta:
        model = Reservation
        fields = ["customer_name", "phone", "email", "party_size", "reservation_date", "reservation_time", "notes"]
        labels = {
            "customer_name": "Nombre completo",
            "phone": "Teléfono",
            "email": "Correo electrónico",
            "party_size": "Cantidad de personas",
            "notes": "Solicitudes especiales",
        }
        widgets = {
            "customer_name": forms.TextInput(attrs={"placeholder": "Tu nombre"}),
            "phone": forms.NumberInput(attrs={"inputmode": "numeric", "min": "0", "step": "1", "placeholder": "88888888"}),
            "email": forms.EmailInput(attrs={"placeholder": "correo@ejemplo.com"}),
            "party_size": forms.NumberInput(attrs={"min": 1, "max": 20, "step": 1}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, language="es", **kwargs):
        self.language = language or "es"
        super().__init__(*args, **kwargs)
        self._apply_language()
        self.fields["reservation_time"].choices = self._build_time_choices()

    def _apply_language(self):
        if self.language == "en":
            self.fields["customer_name"].label = "Full name"
            self.fields["phone"].label = "Phone number"
            self.fields["email"].label = "Email"
            self.fields["party_size"].label = "Party size"
            self.fields["reservation_date"].label = "Date"
            self.fields["reservation_time"].label = "Time"
            self.fields["notes"].label = "Special requests"
            self.fields["customer_name"].widget.attrs["placeholder"] = "Your name"
            self.fields["email"].widget.attrs["placeholder"] = "email@example.com"
            self.fields["phone"].widget.attrs["placeholder"] = "88888888"

    def _build_time_choices(self):
        restaurant = get_active_restaurant()
        selected_date = None
        raw_date = None

        if self.is_bound:
            raw_date = self.data.get("reservation_date")
        elif self.initial.get("reservation_date"):
            raw_date = self.initial.get("reservation_date")
        elif getattr(self.instance, "reservation_date", None):
            selected_date = self.instance.reservation_date

        if raw_date and not selected_date:
            try:
                selected_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
            except ValueError:
                selected_date = None

        if not selected_date:
            selected_date = datetime.today().date()

        weekday = selected_date.weekday()
        windows = restaurant.business_hours.filter(weekday=weekday, is_open=True).order_by("opens_at")
        choices = []
        for window in windows:
            cursor = datetime.combine(selected_date, window.opens_at)
            end_dt = datetime.combine(selected_date, window.closes_at)
            while cursor < end_dt:
                label = cursor.strftime("%H:%M")
                choices.append((label, label))
                cursor += timedelta(minutes=15)
        return choices

    def clean_party_size(self):
        value = self.cleaned_data["party_size"]
        if value < 1:
            raise ValidationError("La cantidad debe ser al menos 1." if self.language != "en" else "Party size must be at least 1.")
        if value > 20:
            raise ValidationError("Para grupos muy grandes, contacta directamente al restaurante." if self.language != "en" else "For very large groups, please contact the restaurant directly.")
        return value

    def clean_reservation_time(self):
        value = self.cleaned_data["reservation_time"]
        if value.minute % 15 != 0:
            raise ValidationError("Selecciona un horario en intervalos de 15 minutos." if self.language != "en" else "Please select a time in 15-minute intervals.")
        return value

    def clean(self):
        cleaned = super().clean()
        d = cleaned.get("reservation_date")
        t = cleaned.get("reservation_time")
        p = cleaned.get("party_size")
        if d and t and p:
            restaurant = get_active_restaurant()
            exclude_id = self.instance.pk if getattr(self.instance, "pk", None) else None
            validate_reservation(restaurant, d, t, p, exclude_id=exclude_id)
        return cleaned


class PublicReservationForm(BaseReservationForm):
    def clean_party_size(self):
        value = super().clean_party_size()
        if value > 6:
            restaurant = get_active_restaurant()
            whatsapp = restaurant.whatsapp_number or restaurant.phone or ""
            if self.language == "en":
                raise ValidationError(
                    f"Online reservations are not available for groups larger than 6 people. Please contact us on WhatsApp ({whatsapp}) and we will gladly help you."
                )
            raise ValidationError(
                f"Las reservas en línea no están disponibles para grupos mayores a 6 personas. Por favor contáctanos por WhatsApp ({whatsapp}) y con gusto te ayudamos."
            )
        return value


class TableChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name} · {obj.capacity} pax"


class StaffReservationForm(BaseReservationForm):
    assigned_table = TableChoiceField(
        queryset=RestaurantTable.objects.none(),
        required=False,
        empty_label="Asignación automática",
        label="Mesa (opcional)",
    )

    class Meta(BaseReservationForm.Meta):
        fields = BaseReservationForm.Meta.fields + ["assigned_table", "internal_notes", "status"]
        labels = {**BaseReservationForm.Meta.labels, "internal_notes": "Notas internas", "status": "Estado"}
        widgets = {**BaseReservationForm.Meta.widgets, "internal_notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, language=language, **kwargs)
        restaurant = get_active_restaurant()
        self.fields["assigned_table"].queryset = restaurant.tables.filter(is_active=True).order_by("capacity", "name")
        self.fields["assigned_table"].help_text = (
            "Opcional. Si no eliges una mesa, el sistema asignará la mejor disponible."
            if self.language != "en"
            else "Optional. If you do not select a table, the system will assign the best available one."
        )
        if self.language == "en":
            self.fields["assigned_table"].label = "Table (optional)"
            self.fields["assigned_table"].empty_label = "Automatic assignment"
            self.fields["internal_notes"].label = "Internal notes"
            self.fields["status"].label = "Status"

    def clean(self):
        cleaned = super().clean()
        d = cleaned.get("reservation_date")
        t = cleaned.get("reservation_time")
        p = cleaned.get("party_size")
        selected_table = cleaned.get("assigned_table")
        if d and t and p:
            restaurant = get_active_restaurant()
            exclude_id = self.instance.pk if getattr(self.instance, "pk", None) else None
            validate_reservation(
                restaurant,
                d,
                t,
                p,
                exclude_id=exclude_id,
                selected_table=selected_table,
            )
        return cleaned


class ReservationStatusForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["status", "internal_notes", "attended"]
        widgets = {"internal_notes": forms.Textarea(attrs={"rows": 3})}
