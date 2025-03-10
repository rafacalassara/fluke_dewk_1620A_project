# fluke_data/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CalibrationCertificateModel(models.Model):
    calibration_date = models.DateField()
    next_calibration_date = models.DateField()
    certificate_number = models.CharField(max_length=100)

    # Temperature calibration points
    temp_indication_point_1 = models.FloatField()
    temp_correction_1 = models.FloatField()
    temp_indication_point_2 = models.FloatField()
    temp_correction_2 = models.FloatField()
    temp_indication_point_3 = models.FloatField()
    temp_correction_3 = models.FloatField()

    # Humidity calibration points
    humidity_indication_point_1 = models.FloatField()
    humidity_correction_1 = models.FloatField()
    humidity_indication_point_2 = models.FloatField()
    humidity_correction_2 = models.FloatField()
    humidity_indication_point_3 = models.FloatField()
    humidity_correction_3 = models.FloatField()

    # Uncertainty values
    temp_uncertainty = models.FloatField()
    humidity_uncertainty = models.FloatField()

    class Meta:
        ordering = ['-calibration_date']

    def __str__(self):
        return f"{self.certificate_number} on {self.calibration_date}"


class ThermohygrometerModel(models.Model):
    ip_address = models.CharField(max_length=100)
    is_connected = models.BooleanField(default=False)
    time_interval_to_save_measures = models.IntegerField(default=5)
    equipment_fisical_location = models.CharField(max_length=100, null=True, blank=True, default='')
    pn = models.CharField(max_length=100)
    sn = models.CharField(max_length=100)
    instrument_name = models.CharField(max_length=100)
    group_name = models.CharField(max_length=100, null=True, blank=True)
    last_connection_attempt = models.DateTimeField(null=True, blank=True)

    # For backward compatibility
    min_temperature = models.FloatField(null=True, blank=True, help_text="Minimum acceptable temperature value - moved to sensor level")
    max_temperature = models.FloatField(null=True, blank=True, help_text="Maximum acceptable temperature value - moved to sensor level")
    min_humidity = models.FloatField(null=True, blank=True, help_text="Minimum acceptable humidity value - moved to sensor level")
    max_humidity = models.FloatField(null=True, blank=True, help_text="Maximum acceptable humidity value - moved to sensor level")

    def __str__(self):
        return f"{self.instrument_name} (PN: {self.pn}, SN: {self.sn})"
    
    def delete(self, *args, **kwargs):
        # Before deleting, update related Measures with the pn and sn
        MeasuresModel.objects.filter(instrument=self).update(pn=self.pn, sn=self.sn)
        super().delete(*args, **kwargs)


class SensorModel(models.Model):
    instrument = models.ForeignKey(ThermohygrometerModel, on_delete=models.CASCADE, related_name='sensors')
    sensor_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, help_text="Room or location where the sensor is placed", null=True, blank=True)
    sensor_sn = models.CharField(max_length=100, null=True, blank=True)
    sensor_pn = models.CharField(max_length=100, null=True, blank=True)
    channel = models.IntegerField(choices=((1, 'Channel 1'), (2, 'Channel 2')), default=1)
    
    # Measurement Limits for this specific sensor
    min_temperature = models.FloatField(null=True, blank=True, help_text="Minimum acceptable temperature value")
    max_temperature = models.FloatField(null=True, blank=True, help_text="Maximum acceptable temperature value")
    min_humidity = models.FloatField(null=True, blank=True, help_text="Minimum acceptable humidity value")
    max_humidity = models.FloatField(null=True, blank=True, help_text="Maximum acceptable humidity value")
    
    # Add calibration certificate field to sensor
    calibration_certificate = models.ForeignKey(CalibrationCertificateModel, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = [['instrument', 'channel']]
    
    def __str__(self):
        return f"Channel: {self.channel} - {self.location}"


class MeasuresModel(models.Model):
    instrument = models.ForeignKey(ThermohygrometerModel, on_delete=models.CASCADE, null=True)
    temperature = models.FloatField(editable=False)
    corrected_temperature = models.FloatField(editable=False, null=True, blank=True)
    humidity = models.FloatField(editable=False)
    corrected_humidity = models.FloatField(editable=False, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    pn = models.CharField(max_length=100, blank=True, null=True, editable=False)
    sn = models.CharField(max_length=100, blank=True, null=True, editable=False)
    sensor = models.ForeignKey(SensorModel, on_delete=models.CASCADE, null=True, related_name='measures')


class CustomUser(AbstractUser):
    name = models.CharField(max_length=100)
    is_manager = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # Set 'name' to the same value as 'username' before saving
        if not self.name:
            self.name = self.username
        super().save(*args, **kwargs)