# fluke_dewk_1620A_project\thermohygrometer\thermohygrometer.py

import pyvisa
import time
from datetime import datetime

class Thermohygrometer:
    def __init__(self, ip, port=10001):
        self.ip_address = ip
        self.port = port
        self.rm = pyvisa.ResourceManager()
        
        self.instrument = None
        self._format_data = None

    def connect(self):
        try:
            self.instrument = self.rm.open_resource(f'TCPIP0::{self.ip_address}::{self.port}::SOCKET')
            self.instrument.timeout = 2000  # Timeout de 5 segundos
            self.instrument.read_termination = '\r'
            self.instrument.write_termination = '\r'
            self.set_format_data()
            self.get_format_data()
            idn = self.instrument.query('*IDN?')
            return idn
        except Exception as e:
            print(f"Error connecting to DewK 1620A at {self.ip_address}: {e}")
            self.instrument = None
            return False

    def disconnect(self):
        if self.instrument:
            self.instrument.close()
        self.instrument = None
        self.rm.close()
        time.sleep(0.25)

    def send_command(self, command):
        if not self.instrument:
            print("Thermohygrometer not connected.")
            return None
        try:
            response = self.instrument.query(command)
            return response
        except Exception as e:
            print(f"Error sending command '{command}'to DewK 1620A: {e}")
            return None

    def get_format_data(self):
        response = self.send_command('FORMat:TDST:STATe?')
        self._format_data = response == '1'
        return self._format_data
    
    def set_format_data(self, status: bool = True):
        status = '1' if status else '0'
        self.send_command(f'FORM:TDST:STAT {status}')

    def _parse_live_data_one_channel(self, data: str):
        parsed_data = data.split(',')
        result = {}
        # print(self._format_data, data)
        if self._format_data is True:
            # response format: 1,1,22.86,C,47.4,%,2024,7,17,14,5,15
            parsed_data = parsed_data[2:]  # Skip the first two elements
            result['temperature'] = float(parsed_data.pop(0))
            result['humidity'] = float(parsed_data.pop(1))
            year, month, day, hour, minute, second = map(int, parsed_data[2:])
            date = datetime(year, month, day, hour, minute, second)
            date = date.isoformat().replace('T',' ').replace('-','/')
            result['date'] = date
        else:
            # response format: 22.80,47.3
            result['temperature'] = float(parsed_data[0])
            result['humidity'] = float(parsed_data[1])

        return result
