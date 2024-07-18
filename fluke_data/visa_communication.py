# fluke_data/visa_communication.py
import time 
from thermohygrometer.thermohygrometer import Thermohygrometer

class Instrument(Thermohygrometer):
    def __init__(self, ip_address):
        super().__init__(ip_address)
        self.connect()

    def get_data(self, channel = '1'):
        while True:
            try:
                data = self.instrument.query(f"READ? {channel}")
                data = self._parse_live_data_one_channel(data=data)
                return data
            except Exception as e:
                return str(e)
            time.sleep(2)
