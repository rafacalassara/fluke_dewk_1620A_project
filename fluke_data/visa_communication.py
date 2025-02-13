# fluke_data/visa_communication.py
from asgiref.sync import sync_to_async

from thermohygrometer.thermohygrometer import Thermohygrometer

from .models import ThermohygrometerModel


class Instrument(Thermohygrometer):
    def __init__(self, ip_address):
        super().__init__(ip_address)
        self.connect()
        # Use async method to save data to the database
        sync_to_async(self.save_to_database)()

    def get_data(self, channel='1'):
        """
        Retrieves live data from the specified channel of the thermohygrometer.

        This method continuously attempts to query the instrument for live data, processes it, and returns the result.
        It sends the command `READ?` followed by the channel number to the instrument, then parses the response.
        
        Args:
            channel (str, optional): The channel number to query for data. Defaults to '1'.
        
        Returns:
            dict or str:
                - A dictionary with parsed temperature, humidity, and possibly date (depending on format).
                - If an exception occurs, the exception message is returned as a string.
        
        Exceptions:
            Captures and returns any exception raised during the instrument query or data parsing.
        """
        while True:
            try:
                data = self.instrument.query(f"READ? {channel}")
                data = self._parse_live_data_one_channel(data=data)
                return data
            except Exception as e:
                return str(e)

    def save_to_database(self):
        ThermohygrometerModel.objects.update_or_create(
            ip_address=self.ip_address,
            defaults={
                'pn': self.PN,
                'sn': self.SN,
                'instrument_name': self.INSTRUMENT_NAME,
                'group_name': f"thermo_{self.PN}_{self.SN}",
            }
        )