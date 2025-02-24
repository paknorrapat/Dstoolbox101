from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Treatment)
admin.site.register(Dentist)
admin.site.register(Appointment)
admin.site.register(TreatmentHistory)
admin.site.register(ClosedDay)