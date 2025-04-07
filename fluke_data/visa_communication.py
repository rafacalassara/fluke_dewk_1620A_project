# fluke_data/visa_communication.py
from asgiref.sync import sync_to_async

from thermohygrometer.thermohygrometer import Thermohygrometer

from .models import ThermohygrometerModel, SensorModel


class Instrument(Thermohygrometer):
    def __init__(self, ip_address):
        super().__init__(ip_address)
        self.connect()
        # Use async method to save data to the database
        sync_to_async(self.save_to_database)()

    def get_data(self, channel=None):
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
                data = self._parse_live_data_one_channel(data=data,channel=channel)
                return data
            except Exception as e:
                return str(e)
    
    def get_live_data_all_channels(self):
        """
        Retrieves live data from all available channels of the thermohygrometer.
        
        Returns:
            dict: A dictionary with channel numbers as keys and the corresponding data as values.
                  Each channel's data includes temperature, humidity, and date.
        """
        result = {}
        if self.datetime_adjust_made:
            self.datetime_adjust_made = False
            return result
        
        try:
            # Get data from channel 1
            ch1_data = self.get_data(channel='1')
            if isinstance(ch1_data, dict):
                result[1] = ch1_data
                
            # Get data from channel 2
            ch2_data = self.get_data(channel='2')
            if isinstance(ch2_data, dict):
                result[2] = ch2_data
            return result
        except Exception as e:
            print(f"Error getting data from all channels: {str(e)}")
            return {}

    def save_to_database(self):
        thermo, created = ThermohygrometerModel.objects.update_or_create(
            ip_address=self.ip_address,
            defaults={
                'pn': self.PN,
                'sn': self.SN,
                'instrument_name': self.INSTRUMENT_NAME,
                'group_name': f"thermo_{self.PN}_{self.SN}",
            }
        )
        
        # Create default sensors for both channels if they don't exist
        if created:
            # Create sensor for channel 1 (may already exist for backward compatibility)
            SensorModel.objects.get_or_create(
                instrument=thermo,
                channel=1,
                defaults={
                    'sensor_name': f"{thermo.instrument_name} - Channel 1",
                    'location': 'Default Location',
                    'min_temperature': thermo.min_temperature,
                    'max_temperature': thermo.max_temperature,
                    'min_humidity': thermo.min_humidity,
                    'max_humidity': thermo.max_humidity,
                }
            )
            
            # Create sensor for channel 2
            SensorModel.objects.get_or_create(
                instrument=thermo,
                channel=2,
                defaults={
                    'sensor_name': f"{thermo.instrument_name} - Channel 2",
                    'location': 'Default Location',
                }
            )