# fluke_data/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class ThermohygrometerModel(models.Model):
    ip_address = models.CharField(max_length=100)
    is_connected = models.BooleanField(default=False)
    pn = models.CharField(max_length=100)
    sn = models.CharField(max_length=100)
    instrument_name = models.CharField(max_length=100)
    sensor_sn = models.CharField(max_length=100, null=True, blank=True)
    sensor_pn = models.CharField(max_length=100, null=True, blank=True)
    group_name = models.CharField(max_length=100, null=True, blank=True)  # Add this line


    def __str__(self):
        return f"{self.instrument_name} (PN: {self.pn}, SN: {self.sn})"
    
    def delete(self, *args, **kwargs):
        # Before deleting, update related Measures with the pn and sn
        MeasuresModel.objects.filter(instrument=self).update(pn=self.pn, sn=self.sn)
        super().delete(*args, **kwargs)


class MeasuresModel(models.Model):
    instrument = models.ForeignKey(ThermohygrometerModel, on_delete=models.SET_NULL, null=True)
    temperature = models.FloatField(editable=False)
    humidity = models.FloatField(editable=False)
    date = models.DateTimeField(editable=False)
    pn = models.CharField(max_length=100, blank=True, null=True, editable=False)
    sn = models.CharField(max_length=100, blank=True, null=True, editable=False)
    sensor_sn = models.CharField(max_length=100, null=True, blank=True, editable=False)
    sensor_pn = models.CharField(max_length=100, null=True, blank=True, editable=False)

class CustomUser(AbstractUser):
    name = models.CharField(max_length=100)
    is_manager = models.BooleanField(default=False)
