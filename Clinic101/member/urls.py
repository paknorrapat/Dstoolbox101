from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('appointment/<int:dentist_id>/',appointment_view,name='appointment'),
    path('get-time-slots/',get_time_slots,name='get_time_slots'),
    path('calendar/', calendar_view, name='calendar'),

    path('member_home',member_home,name='member-home'),
    path("appointment/delete/<int:id>/",delete_appointment_member,name="member-appointment-delete"),
    path("appointment/edit/<int:id>/",edit_appointment_member,name="member-appointment-edit"),

    path('select-appointment-date/<int:appointment_id>/',select_appointment_date, name='select-appointment-date'),
    path('t_history/<int:user_id>/',t_history,name="t-history"),
    path('braces_progress/<int:user_id>/',braces_progress,name="braces-progress"),

    path('appointment_all/',appointment_all,name="appointment-all"),
]
