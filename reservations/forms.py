from django import forms
from django.core.exceptions import ValidationError
from restaurant.models import RestaurantTable
from .models import Reservation
from .validators import validate_not_past_day
from .services import get_active_restaurant, validate_reservation

class BaseReservationForm(forms.ModelForm):
    reservation_date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}), validators=[validate_not_past_day], label="Fecha")
    reservation_time = forms.TimeField(widget=forms.TimeInput(attrs={"type":"time"}), label="Hora")

    class Meta:
        model = Reservation
        fields = ["customer_name","phone","email","party_size","reservation_date","reservation_time","notes"]
        labels = {
            "customer_name":"Nombre completo",
            "phone":"Teléfono",
            "email":"Correo electrónico",
            "party_size":"Cantidad de personas",
            "notes":"Solicitudes especiales",
        }
        widgets = {"notes": forms.Textarea(attrs={"rows":3})}

    def clean_party_size(self):
        value = self.cleaned_data["party_size"]
        if value < 1:
            raise ValidationError("La cantidad debe ser al menos 1.")
        if value > 20:
            raise ValidationError("Para grupos grandes, contacta directamente al restaurante.")
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
    pass

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
        fields = BaseReservationForm.Meta.fields + ["assigned_table", "internal_notes","status"]
        labels = {**BaseReservationForm.Meta.labels, "internal_notes":"Notas internas", "status":"Estado"}
        widgets = {**BaseReservationForm.Meta.widgets, "internal_notes": forms.Textarea(attrs={"rows":3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        restaurant = get_active_restaurant()
        self.fields["assigned_table"].queryset = restaurant.tables.filter(is_active=True).order_by("capacity", "name")
        self.fields["assigned_table"].help_text = "Opcional. Si no eliges una mesa, el sistema asignará la mejor disponible."

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
        fields = ["status","internal_notes","attended"]
        widgets = {"internal_notes": forms.Textarea(attrs={"rows":3})}
