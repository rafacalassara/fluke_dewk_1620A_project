from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ThermohygrometerModel)
admin.site.register(MeasuresModel)
admin.site.register(CustomUser)