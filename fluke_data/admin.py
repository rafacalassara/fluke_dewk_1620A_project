from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(ThermohygrometerModel)
# admin.site.register(MeasuresModel)
admin.site.register(CalibrationCertificateModel)
admin.site.register(CustomUser)

class MeasuresModelAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'temperature', 'corrected_temperature', 'humidity', 
                    'corrected_humidity', 'date', 'pn', 'sn', 'sensor_sn', 'sensor_pn')
    
admin.site.register(MeasuresModel, MeasuresModelAdmin)
