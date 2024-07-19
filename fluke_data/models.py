# fluke_data/models.py
from django.db import models

class Thermohygrometer(models.Model):
    ip_address = models.CharField(max_length=100)
    pn = models.CharField(max_length=100)
    sn = models.CharField(max_length=100)
    instrument_name = models.CharField(max_length=100)
    sensor_sn = models.CharField(max_length=100, null=True, blank=True)
    sensor_pn = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.instrument_name} (PN: {self.pn}, SN: {self.sn})"
