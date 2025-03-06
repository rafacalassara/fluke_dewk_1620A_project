from django.contrib import admin

from .models import *

# Register your models here.
class SensorInline(admin.TabularInline):
    model = SensorModel
    extra = 0

class ThermohygrometerAdmin(admin.ModelAdmin):
    list_display = ['instrument_name', 'ip_address', 'pn', 'sn', 'is_connected', 'calibration_certificate']
    search_fields = ['instrument_name', 'ip_address', 'pn', 'sn']
    inlines = [SensorInline]

admin.site.register(ThermohygrometerModel, ThermohygrometerAdmin)
admin.site.register(CalibrationCertificateModel)
admin.site.register(CustomUser)
admin.site.register(SensorModel)

class MeasuresModelAdmin(admin.ModelAdmin):
    list_display = ['date', 'instrument', 'sensor', 'temperature', 'corrected_temperature', 'humidity', 'corrected_humidity', 'pn', 'sn', 'get_sensor_sn', 'get_sensor_pn']
    list_filter = ['date', 'instrument', 'sensor']
    search_fields = ['instrument__name', 'pn', 'sn', 'sensor__sensor_name', 'sensor__location']
    ordering = ['-date']
    
    def get_sensor_sn(self, obj):
        if obj.sensor:
            return obj.sensor.sensor_sn
        return None
    get_sensor_sn.short_description = 'Sensor SN'
    
    def get_sensor_pn(self, obj):
        if obj.sensor:
            return obj.sensor.sensor_pn
        return None
    get_sensor_pn.short_description = 'Sensor PN'

admin.site.register(MeasuresModel, MeasuresModelAdmin)
