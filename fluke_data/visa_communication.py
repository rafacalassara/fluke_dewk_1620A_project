# fluke_data/visa_communication.py
import time 
from thermohygrometer.thermohygrometer import Thermohygrometer
from .models import ThermohygrometerModel
from asgiref.sync import sync_to_async

class Instrument(Thermohygrometer):
    def __init__(self, ip_address):
        super().__init__(ip_address)
        self.connect()
        # Use async method to save data to the database
        sync_to_async(self.save_to_database)()

    def get_data(self, channel='1'):
        while True:
            try:
                data = self.instrument.query(f"READ? {channel}")
                data = self._parse_live_data_one_channel(data=data)
                return data
            except Exception as e:
                return str(e)
            time.sleep(2)

    def save_to_database(self):
        ThermohygrometerModel.objects.update_or_create(
            ip_address=self.ip_address,
            defaults={
                'pn': self.PN,
                'sn': self.SN,
                'instrument_name': self.INSTRUMENT_NAME
            }
        )
