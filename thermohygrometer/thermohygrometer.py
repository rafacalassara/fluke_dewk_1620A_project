# fluke_dewk_1620A_project\thermohygrometer\thermohygrometer.py

import pyvisa
import time
from datetime import datetime

class Thermohygrometer:
    SN: str
    PN: str
    INSTRUMENT_NAME: str
    SENSOR_SN: str
    SENSOR_PN: str
    GROUP_NAME: str = ''

    def __init__(self, ip, port=10001):
        self.ip_address = ip
        self.port = port
        self.rm = pyvisa.ResourceManager()

        self.instrument = None
        self._format_data = None

    def connect(self):
        try:
            self.instrument = self.rm.open_resource(f'TCPIP0::{self.ip_address}::{self.port}::SOCKET')
        except pyvisa.errors.VisaIOError as e:
            print(f"Error connecting to DewK 1620A at {self.ip_address}: {e}")
            self.instrument = None
            return False
        
        self.instrument.timeout = 2000  # Timeout de 2 segundos
        self.instrument.read_termination = '\r'
        self.instrument.write_termination = '\r'
        self.set_format_data()
        self.get_format_data()
        self.get_instrument_personal_info()

    def disconnect(self):
        if self.instrument is not None:
            self.instrument.close()
        self.instrument = None
        time.sleep(0.25)

    def send_command(self, command, response_needed=True):
        if not self.instrument:
            print("Thermohygrometer not connected.")
            return None
        try:
            response = self.instrument.query(command) if response_needed else self.instrument.write(command)
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
        self.send_command(f'FORM:TDST:STAT {status}', response_needed=False)

    def _parse_live_data_one_channel(self, data: str):
        parsed_data = data.split(',')
        result = {}
        if self._format_data is True:
            # response format: 1,1,22.86,C,47.4,%,2024,7,17,14,5,15
            parsed_data = parsed_data[2:]  # Skip the first two elements
            result['temperature'] = float(parsed_data.pop(0))
            result['humidity'] = float(parsed_data.pop(1))
            year, month, day, hour, minute, second = map(int, parsed_data[2:])
            date = datetime(year, month, day, hour, minute, second)
            date = date.isoformat().replace('T',' ').replace('-','/')
            result['date'] = date
            # returns : 
        else:
            # response format: 22.80,47.3
            result['temperature'] = float(parsed_data[0])
            result['humidity'] = float(parsed_data[1])

        return result

    def get_instrument_personal_info(self):
        idn = self.send_command('*IDN?')
        _,self.PN,self.SN,_ = idn.split(',')
        time.sleep(0.25)
        self.INSTRUMENT_NAME = self.send_command('SENSor1:IDENtification?').replace('"','')
        self.GROUP_NAME = f"thermo_{self.PN}_{self.SN}"
        print(f'Conected to PN: {self.PN}, SN: {self.SN}, Name: {self.INSTRUMENT_NAME}')
        
