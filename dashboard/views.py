from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render
from datetime import date
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView

from reservations.forms import StaffReservationForm, ReservationStatusForm
from reservations.models import Reservation
from reservations.services import get_active_restaurant, assign_table_for_reservation
from restaurant.forms import RestaurantProfileForm, BlockedDateForm, BlockedTimeSlotForm, BusinessHourForm, RestaurantTableForm
from restaurant.models import RestaurantTable
from .services import summary_data, build_availability_by_slot, build_availability_by_table
from .utils import owner_required

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard_home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(summary_data())
        return context

class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'dashboard/reservations_list.html'
    context_object_name = 'reservations'
    paginate_by = 20

    def get_queryset(self):
        qs = Reservation.objects.select_related("assigned_table").order_by('reservation_date','reservation_time')
        status = self.request.GET.get('status')
        q = self.request.GET.get('q')
        date = self.request.GET.get('date')
        scope = self.request.GET.get('scope')
        if scope == 'today':
            qs = qs.filter(reservation_date=timezone.localdate())
        if status:
            qs = qs.filter(status=status)
        if date:
            qs = qs.filter(reservation_date=date)
        if q:
            qs = qs.filter(Q(customer_name__icontains=q) | Q(phone__icontains=q))
        return qs

class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = 'dashboard/reservation_detail.html'
    context_object_name = 'reservation'

@login_required
def reservation_create_manual(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = StaffReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.restaurant = get_active_restaurant()
            reservation.created_by_staff = True
            assign_table_for_reservation(reservation)
            reservation.save()
            mesa_msg = reservation.assigned_table.name if reservation.assigned_table else "Sin asignar"
            messages.success(request, f'Reserva creada correctamente. Mesa asignada: {mesa_msg}.')
            return redirect('dashboard:reservations')
    else:
        form = StaffReservationForm(initial={'status': Reservation.STATUS_CONFIRMED})
    return render(request, 'dashboard/reservation_form_internal.html', {'form': form, 'title': 'Nueva reserva manual'})

@login_required
def reservation_edit(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        form = StaffReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            reservation = form.save(commit=False)
            assign_table_for_reservation(reservation)
            reservation.save()
            mesa_msg = reservation.assigned_table.name if reservation.assigned_table else "Sin asignar"
            messages.success(request, f'Reserva actualizada. Mesa: {mesa_msg}.')
            return redirect('dashboard:reservation_detail', pk=reservation.pk)
    else:
        form = StaffReservationForm(instance=reservation)
    return render(request, 'dashboard/reservation_form_internal.html', {'form': form, 'title': 'Editar reserva', 'reservation': reservation})

@login_required
def reservation_inline_status(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method != 'POST':
        return redirect('dashboard:reservations')
    new_status = request.POST.get('status')
    allowed = {choice[0] for choice in Reservation.STATUS_CHOICES}
    if new_status not in allowed:
        messages.error(request, 'Estado inválido.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard:reservations'))
    reservation.status = new_status
    reservation.attended = new_status == Reservation.STATUS_COMPLETED
    reservation.save(update_fields=['status', 'attended', 'updated_at'])
    messages.success(request, f'Estado de {reservation.customer_name} actualizado a {reservation.get_status_display()}.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:reservations'))

@login_required
def reservation_quick_status(request, pk, status):
    reservation = get_object_or_404(Reservation, pk=pk)
    allowed = {
        'confirm': Reservation.STATUS_CONFIRMED,
        'cancel': Reservation.STATUS_CANCELLED,
        'complete': Reservation.STATUS_COMPLETED,
        'noshow': Reservation.STATUS_NO_SHOW,
    }
    new_status = allowed.get(status)
    if not new_status:
        messages.error(request, 'Acción inválida.')
        return redirect('dashboard:reservations')
    reservation.status = new_status
    reservation.attended = new_status == Reservation.STATUS_COMPLETED
    reservation.save()
    messages.success(request, 'Estado actualizado.')
    return redirect('dashboard:reservation_detail', pk=reservation.pk)

@login_required
def reservation_notes(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        form = ReservationStatusForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notas y estado actualizados.')
            return redirect('dashboard:reservation_detail', pk=reservation.pk)
    else:
        form = ReservationStatusForm(instance=reservation)
    return render(request, 'dashboard/reservation_status_form.html', {'form': form, 'reservation': reservation})

@login_required
def availability_view(request):
    target_date = request.GET.get("date") or timezone.localdate()
    try:
        if isinstance(target_date, str):
            target_date = date.fromisoformat(str(target_date))
    except Exception:
        target_date = timezone.localdate()
    mode = request.GET.get("mode", "franja")
    if mode == "mesa":
        data = build_availability_by_table(target_date=target_date)
        context = {
            "mode": mode,
            "target_date": target_date,
            "availability_rows": data["rows"],
            "tables": data["tables"],
            "slot_headers": data["slot_headers"],
        }
    else:
        context = {
            "mode": "franja",
            "target_date": target_date,
            "availability_rows": build_availability_by_slot(target_date=target_date),
        }
    return render(request, "dashboard/availability.html", context)

@login_required
@owner_required
def settings_view(request):
    restaurant = get_active_restaurant()
    if request.method == 'POST':
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada.')
            return redirect('dashboard:settings')
    else:
        form = RestaurantProfileForm(instance=restaurant)
    hours = restaurant.business_hours.order_by('weekday','opens_at')
    tables = restaurant.tables.order_by('capacity', 'name')
    table_form = RestaurantTableForm()
    return render(request, 'dashboard/settings.html', {'form': form, 'hours': hours, 'tables': tables, 'table_form': table_form})

@login_required
@owner_required
def business_hour_create(request):
    restaurant = get_active_restaurant()
    if request.method == 'POST':
        form = BusinessHourForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.restaurant = restaurant
            obj.save()
            messages.success(request, 'Horario agregado.')
            return redirect('dashboard:settings')
    else:
        form = BusinessHourForm()
    return render(request, 'dashboard/business_hour_form.html', {'form': form})

@login_required
@owner_required
def table_create(request):
    restaurant = get_active_restaurant()
    if request.method == "POST":
        form = RestaurantTableForm(request.POST)
        if form.is_valid():
            table = form.save(commit=False)
            table.restaurant = restaurant
            table.save()
            messages.success(request, "Mesa agregada correctamente.")
    return redirect("dashboard:settings")

@login_required
@owner_required
def table_toggle_active(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk, restaurant=get_active_restaurant())
    table.is_active = not table.is_active
    table.save(update_fields=["is_active"])
    messages.success(request, "Estado de la mesa actualizado.")
    return redirect("dashboard:settings")

@login_required
@owner_required
def blocked_slots_view(request):
    restaurant = get_active_restaurant()
    return render(request, 'dashboard/blocked_slots.html', {
        'blocked_dates': restaurant.blocked_dates.all(),
        'blocked_slots': restaurant.blocked_slots.all(),
        'date_form': BlockedDateForm(),
        'slot_form': BlockedTimeSlotForm(),
    })

@login_required
@owner_required
def blocked_date_create(request):
    restaurant = get_active_restaurant()
    if request.method == 'POST':
        form = BlockedDateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.restaurant = restaurant
            obj.save()
            messages.success(request, 'Fecha bloqueada agregada.')
    return redirect('dashboard:blocked_slots')

@login_required
@owner_required
def blocked_slot_create(request):
    restaurant = get_active_restaurant()
    if request.method == 'POST':
        form = BlockedTimeSlotForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.restaurant = restaurant
            obj.save()
            messages.success(request, 'Bloqueo horario agregado.')
    return redirect('dashboard:blocked_slots')

@login_required
@owner_required
def user_list(request):
    users = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'dashboard/users.html', {'users': users})

@login_required
@owner_required
def user_create(request):
    UserForm = modelform_factory(User, fields=('username','first_name','last_name','email','is_active'))
    if request.method == 'POST':
        form = UserForm(request.POST)
        password = request.POST.get('password')
        if form.is_valid() and password:
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = False
            user.set_password(password)
            user.save()
            messages.success(request, 'Usuario staff creado.')
            return redirect('dashboard:users')
    else:
        form = UserForm()
    return render(request, 'dashboard/user_form.html', {'form': form})

@login_required
@owner_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk, is_superuser=False)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, 'Estado del usuario actualizado.')
    return redirect('dashboard:users')
