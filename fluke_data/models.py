# fluke_data/models.py
from django.db import models

class ThermohygrometerModel(models.Model):
    ip_address = models.CharField(max_length=100)
    pn = models.CharField(max_length=100)
    sn = models.CharField(max_length=100)
    instrument_name = models.CharField(max_length=100)
    sensor_sn = models.CharField(max_length=100, null=True, blank=True)
    sensor_pn = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.instrument_name} (PN: {self.pn}, SN: {self.sn})"
    

class MeasuresModel(models.Model):
    pn_sn = models.CharField(max_length=200)  # Composite field for pn and sn
    temperature = models.FloatField()
    humidity = models.FloatField()
    date = models.DateTimeField()

    def __str__(self):
        return f"Measure for {self.pn_sn} on {self.date.strftime('%Y-%m-%d %H:%M:%S')}"

    def save(self, *args, **kwargs):
        # Automatically set the pn_sn to be a combination of pn and sn
        thermohygrometer = ThermohygrometerModel.objects.filter(pn=self.pn_sn.split('_')[0], sn=self.pn_sn.split('_')[1]).first()
        if thermohygrometer:
            self.pn_sn = f"{thermohygrometer.pn}_{thermohygrometer.sn}"
        super().save(*args, **kwargs)
