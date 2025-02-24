from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("staff_home/",staff_home,name="staff-home"),
    path("appointment/delete/<int:id>/",delete_appointment,name="appointment-delete"),
    path("appointment/add/<int:user_id>/",add_appointment,name="appointment-add"),
    path('appointment/update/<int:appointment_id>/',update_appointment, name='appointment-update'),
    
    path("dentist_manage/",dentist_manage,name="dentist-manage"),
    path("add_dentist/",add_dentist,name="add-dentist"),
    path("delete_dentist/<int:dentist_id>/",delete_dentist,name="delete-dentist"),
    path("edit_dentist/<int:dentist_id>/",edit_dentist,name="edit-dentist"),

    path("treatment_manage/",treatment_manage,name="treatment-manage"),
    path("add_treatment/",add_treatment,name="add-treatment"),
    path("delete_treatment/<int:treatment_id>/",delete_treatment,name="delete-treatment"),
    path("edit_treatment/<int:treatment_id>/",edit_treatment,name="edit-treatment"),


    path("appointment_list/",appointment_list,name="appointment-list"),
    path("member_info/",member_info,name="member-info"),

    path('closed_day/',close_0ff_day,name="closed-day"),
    path('delete_closed_day/<int:pk>/',delete_closed_day, name='delete-closed-day'),
    path('closed_day_list/',closed_day_list,name='closed-day-list'),

    path('update_status_appointment/',update_status_appointment,name='update-status-appointment'),


    path("treatment_history/",treatment_history,name="treatment-history"),
    path("add_treatmenthistory/<int:apt_id>/",add_treatment_history,name="add-treatmenthistory"),
    path('t_history_all/',t_history_all,name='t-history-all'),
    path('update_t_history/<int:treatment_history_id>/',update_treatment_history,name='update-t-history'),

]