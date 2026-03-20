from collections import Counter
from datetime import date

from django.db.models import Avg, Count
from django.utils import timezone

from reservations.models import Reservation
from reservations.services import get_active_restaurant, get_day_slots, get_available_tables

def _occupancy_state(free_count, total_count):
    if total_count == 0:
        return "empty"
    if free_count == 0:
        return "full"
    ratio = free_count / total_count
    if ratio <= 0.25:
        return "high"
    if ratio <= 0.6:
        return "medium"
    return "low"


def build_availability_by_slot(target_date=None):
    restaurant = get_active_restaurant()
    target_date = target_date or timezone.localdate()
    slots = get_day_slots(restaurant, target_date)
    active_tables = list(restaurant.tables.filter(is_active=True).order_by("capacity", "name"))
    total_tables = len(active_tables)
    rows = []

    for slot in slots:
        available_tables = list(get_available_tables(restaurant, target_date, slot))
        free_count = len(available_tables)
        capacity_counter = Counter(table.capacity for table in available_tables)

        summary_lines = [
            f"{count} mesa(s) de {cap} pax"
            for cap, count in sorted(capacity_counter.items())
        ]

        rows.append({
            "label": slot.strftime("%H:%M"),
            "free_count": free_count,
            "total_tables": total_tables,
            "free_tables": available_tables,
            "state": _occupancy_state(free_count, total_tables),
            "summary_lines": summary_lines,
        })

    return rows

def build_availability_by_table(target_date=None, table_id=None):
    restaurant = get_active_restaurant()
    target_date = target_date or timezone.localdate()
    tables = list(restaurant.tables.filter(is_active=True).order_by("capacity", "name"))
    slots = get_day_slots(restaurant, target_date)
    matrix_rows = []

    for table in tables:
        slot_cells = []
        for slot in slots:
            available_ids = {available_table.id for available_table in get_available_tables(restaurant, target_date, slot)}
            is_free = table.id in available_ids
            slot_cells.append({
                "label": slot.strftime("%H:%M"),
                "is_free": is_free,
                "state": "low" if is_free else "full",
                "summary": "Disponible" if is_free else "Ocupada",
            })
        matrix_rows.append({
            "table": table,
            "slots": slot_cells,
        })

    return {
        "tables": tables,
        "rows": matrix_rows,
        "slot_headers": [slot.strftime("%H:%M") for slot in slots],
    }

def summary_data():
    today = timezone.localdate()
    today_qs = Reservation.objects.filter(reservation_date=today)
    month_qs = Reservation.objects.filter(reservation_date__month=today.month, reservation_date__year=today.year)
    return {
        "today_count": today_qs.exclude(status=Reservation.STATUS_CANCELLED).count(),
        "pending_count": today_qs.filter(status=Reservation.STATUS_PENDING).count() + today_qs.filter(status=Reservation.STATUS_CONFIRMED, assigned_table__isnull=True).count(),
        "completed_today": today_qs.filter(status=Reservation.STATUS_COMPLETED).count(),
        "no_show_today": today_qs.filter(status=Reservation.STATUS_NO_SHOW).count(),
        "month_count": month_qs.count(),
        "avg_party_size": round(month_qs.aggregate(avg=Avg("party_size"))["avg"] or 0, 1),
    }
