from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from restaurant.models import RestaurantProfile, BusinessHour, BlockedDate, BlockedTimeSlot, RestaurantTable
from .models import Reservation

ACTIVE_STATUS = [Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED]

def get_active_restaurant():
    restaurant = RestaurantProfile.objects.filter(is_active=True).first()
    if not restaurant:
        raise ValidationError("No hay restaurante activo configurado.")
    return restaurant

def _build_interval(base_date, start_time, duration_minutes):
    start_dt = datetime.combine(base_date, start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    return start_dt, end_dt

def _intervals_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a

def _moment_inside_interval(moment_dt, start_dt, end_dt):
    return start_dt <= moment_dt < end_dt

def validate_business_hours(restaurant, reservation_date, reservation_time):
    weekday = reservation_date.weekday()
    ok = BusinessHour.objects.filter(
        restaurant=restaurant,
        weekday=weekday,
        is_open=True,
        opens_at__lte=reservation_time,
        closes_at__gt=reservation_time,
    ).exists()
    if not ok:
        raise ValidationError("La hora elegida está fuera del horario del restaurante.")

def validate_blocked_date(restaurant, reservation_date):
    if BlockedDate.objects.filter(restaurant=restaurant, date=reservation_date, is_active=True).exists():
        raise ValidationError("La fecha seleccionada está bloqueada.")

def validate_blocked_time(restaurant, reservation_date, reservation_time):
    blocked = BlockedTimeSlot.objects.filter(
        restaurant=restaurant,
        date=reservation_date,
        is_active=True,
        start_time__lte=reservation_time,
        end_time__gt=reservation_time,
    ).exists()
    if blocked:
        raise ValidationError("La hora seleccionada está bloqueada.")

def get_table_assignments_for_booking(restaurant, reservation_date, reservation_time, exclude_id=None):
    qs = Reservation.objects.filter(
        restaurant=restaurant,
        reservation_date=reservation_date,
        status__in=ACTIVE_STATUS,
        assigned_table__isnull=False,
    ).select_related("assigned_table")
    if exclude_id:
        qs = qs.exclude(id=exclude_id)

    new_start, new_end = _build_interval(
        reservation_date,
        reservation_time,
        restaurant.reservation_duration_minutes,
    )

    occupied_table_ids = set()
    for reservation in qs:
        existing_start, existing_end = _build_interval(
            reservation.reservation_date,
            reservation.reservation_time,
            restaurant.reservation_duration_minutes,
        )
        if _intervals_overlap(existing_start, existing_end, new_start, new_end):
            occupied_table_ids.add(reservation.assigned_table_id)
    return occupied_table_ids

def get_table_assignments_for_display(
    restaurant,
    reservation_date,
    display_time,
    interval_minutes=30,
    exclude_id=None,
):
    qs = Reservation.objects.filter(
        restaurant=restaurant,
        reservation_date=reservation_date,
        status__in=ACTIVE_STATUS,
        assigned_table__isnull=False,
    ).select_related("assigned_table")

    if exclude_id:
        qs = qs.exclude(id=exclude_id)

    display_start = datetime.combine(reservation_date, display_time)
    display_end = display_start + timedelta(minutes=interval_minutes)

    occupied_table_ids = set()

    for reservation in qs:
        reservation_start, reservation_end = _build_interval(
            reservation.reservation_date,
            reservation.reservation_time,
            restaurant.reservation_duration_minutes,
        )

        # Traslape real entre la franja visual y la reserva real
        if display_start < reservation_end and display_end > reservation_start:
            occupied_table_ids.add(reservation.assigned_table_id)

    return occupied_table_ids

def get_available_tables(restaurant, reservation_date, reservation_time, party_size=None, exclude_id=None):
    occupied_table_ids = get_table_assignments_for_booking(
        restaurant,
        reservation_date,
        reservation_time,
        exclude_id=exclude_id,
    )
    qs = restaurant.tables.filter(is_active=True).exclude(id__in=occupied_table_ids).order_by("capacity", "name")
    if party_size:
        qs = qs.filter(capacity__gte=party_size)
    return qs

def get_available_tables_for_display(
    restaurant,
    reservation_date,
    display_time,
    interval_minutes=30,
):
    occupied_table_ids = get_table_assignments_for_display(
        restaurant,
        reservation_date,
        display_time,
        interval_minutes=interval_minutes,
    )
    return (
        restaurant.tables
        .filter(is_active=True)
        .exclude(id__in=occupied_table_ids)
        .order_by("capacity", "name")
    )

def find_best_table(restaurant, reservation_date, reservation_time, party_size, exclude_id=None):
    table = get_available_tables(
        restaurant=restaurant,
        reservation_date=reservation_date,
        reservation_time=reservation_time,
        party_size=party_size,
        exclude_id=exclude_id,
    ).first()
    if not table:
        raise ValidationError("No hay una mesa disponible para esa cantidad de personas en esa franja horaria.")
    return table

def validate_selected_table(restaurant, reservation_date, reservation_time, party_size, selected_table, exclude_id=None):
    if not selected_table:
        return
    if not selected_table.is_active:
        raise ValidationError("La mesa seleccionada no está activa.")
    if selected_table.restaurant_id != restaurant.id:
        raise ValidationError("La mesa seleccionada no pertenece a este restaurante.")
    if selected_table.capacity < party_size:
        raise ValidationError("La mesa seleccionada no tiene capacidad suficiente para este grupo.")

    available_ids = {
        table.id
        for table in get_available_tables(
            restaurant=restaurant,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            exclude_id=exclude_id,
        )
    }
    if selected_table.id not in available_ids:
        raise ValidationError("La mesa seleccionada no está disponible para esa franja horaria.")

def validate_reservation(restaurant, reservation_date, reservation_time, party_size, exclude_id=None, selected_table=None):
    validate_blocked_date(restaurant, reservation_date)
    validate_business_hours(restaurant, reservation_date, reservation_time)
    validate_blocked_time(restaurant, reservation_date, reservation_time)
    if selected_table:
        validate_selected_table(
            restaurant=restaurant,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            party_size=party_size,
            selected_table=selected_table,
            exclude_id=exclude_id,
        )
    else:
        find_best_table(restaurant, reservation_date, reservation_time, party_size, exclude_id=exclude_id)

def assign_table_for_reservation(reservation):
    restaurant = reservation.restaurant
    if reservation.assigned_table_id:
        validate_selected_table(
            restaurant=restaurant,
            reservation_date=reservation.reservation_date,
            reservation_time=reservation.reservation_time,
            party_size=reservation.party_size,
            selected_table=reservation.assigned_table,
            exclude_id=reservation.pk,
        )
        return reservation

    reservation.assigned_table = find_best_table(
        restaurant=restaurant,
        reservation_date=reservation.reservation_date,
        reservation_time=reservation.reservation_time,
        party_size=reservation.party_size,
        exclude_id=reservation.pk,
    )
    return reservation

def get_day_slots(restaurant, target_date, interval_minutes=15):
    weekday = target_date.weekday()
    hours = restaurant.business_hours.filter(weekday=weekday, is_open=True).order_by("opens_at")
    slots = []
    for window in hours:
        cursor = datetime.combine(target_date, window.opens_at)
        end_dt = datetime.combine(target_date, window.closes_at)
        while cursor < end_dt:
            slots.append(cursor.time())
            cursor += timedelta(minutes=interval_minutes)
    return slots
