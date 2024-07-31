# fluke_data/tasks.py
from celery import shared_task
from .models import ThermohygrometerModel, MeasuresModel
from datetime import datetime

@shared_task
def store_measurement(thermohygrometer_id, temperature, humidity, date):
    thermohygrometer = ThermohygrometerModel.objects.get(id=thermohygrometer_id)
    
    MeasuresModel.objects.create(
        instrument=thermohygrometer,
        temperature=temperature,
        humidity=humidity,
        date=datetime.fromisoformat(date),
        pn=thermohygrometer.pn,
        sn=thermohygrometer.sn
    )
