from django.urls import path
from .views import (
    DashboardHomeView, ReservationListView, ReservationDetailView,
    reservation_create_manual, reservation_edit, reservation_quick_status,
    reservation_inline_status, reservation_notes, settings_view, business_hour_create,
    blocked_slots_view, blocked_date_create, blocked_slot_create,
    user_list, user_create, user_toggle_active, availability_view,
    table_create, table_toggle_active
)

app_name = 'dashboard'
urlpatterns = [
    path('', DashboardHomeView.as_view(), name='home'),
    path('reservas/', ReservationListView.as_view(), name='reservations'),
    path('reservas/nueva/', reservation_create_manual, name='reservation_create_manual'),
    path('reservas/<int:pk>/', ReservationDetailView.as_view(), name='reservation_detail'),
    path('reservas/<int:pk>/editar/', reservation_edit, name='reservation_edit'),
    path('reservas/<int:pk>/estado/', reservation_inline_status, name='reservation_inline_status'),
    path('reservas/<int:pk>/estado/<str:status>/', reservation_quick_status, name='reservation_quick_status'),
    path('reservas/<int:pk>/notas/', reservation_notes, name='reservation_notes'),
    path('disponibilidad/', availability_view, name='availability'),
    path('configuracion/', settings_view, name='settings'),
    path('configuracion/horarios/nuevo/', business_hour_create, name='business_hour_create'),
    path('configuracion/mesas/nueva/', table_create, name='table_create'),
    path('configuracion/mesas/<int:pk>/toggle/', table_toggle_active, name='table_toggle_active'),
    path('bloqueos/', blocked_slots_view, name='blocked_slots'),
    path('bloqueos/fecha/nueva/', blocked_date_create, name='blocked_date_create'),
    path('bloqueos/franja/nueva/', blocked_slot_create, name='blocked_slot_create'),
    path('usuarios/', user_list, name='users'),
    path('usuarios/nuevo/', user_create, name='user_create'),
    path('usuarios/<int:pk>/toggle/', user_toggle_active, name='user_toggle_active'),
]
