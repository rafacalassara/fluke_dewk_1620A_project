# fluke_dewk_1620A_project\thermohygrometer\thermohygrometer.py

import time
from datetime import datetime

import pyvisa


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
            print(f"thermohygrometer.connect: Error connecting to DewK 1620A at {self.ip_address}: {e}")
            self.instrument = None
            return False
        # print(self.instrument.__dict__)
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
        """
        Parses live data received from one channel of the thermohygrometer.

        The function processes the incoming raw data string and extracts temperature, humidity, and timestamp information.
        The format of the incoming data depends on the `_format_data` flag.

        Args:
            data (str): The raw data string received from the thermohygrometer.

        Returns:
            dict: A dictionary containing the parsed temperature, humidity, and (if applicable) date.

            - If `_format_data` is `True`, the expected input format is:
            "1,1,22.86,C,47.4,%,2024,7,17,14,5,15"
            The result will be:
            {
                'temperature': <float>,
                'humidity': <float>,
                'date': <str>  # In "YYYY/MM/DD HH:MM:SS" format
            }

            - If `_format_data` is `False`, the expected input format is:
            "22.80,47.3"
            The result will be:
            {
                'temperature': <float>,
                'humidity': <float>
            }
        """
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
        
    def get_correction(self, calibration_certificate, measurement_type, measured_value):
        """
        Get the correction for a given measurement based on the calibration_certificate's.
        
        :param calibration_certificate: ThermohygrometerModel instance
        :param measurement_type: 'temperature' or 'humidity'
        :param measured_value: The measured value to correct
        :return: The correction value to apply
        """
        
        if not calibration_certificate:
            return 0  # No correction if no calibration is available

        if measurement_type == 'temperature':
            points = [
                (Thermohygrometer.replace_comma(calibration_certificate.temp_indication_point_1), Thermohygrometer.replace_comma(calibration_certificate.temp_correction_1)),
                (Thermohygrometer.replace_comma(calibration_certificate.temp_indication_point_2), Thermohygrometer.replace_comma(calibration_certificate.temp_correction_2)),
                (Thermohygrometer.replace_comma(calibration_certificate.temp_indication_point_3), Thermohygrometer.replace_comma(calibration_certificate.temp_correction_3)),
            ]
        elif measurement_type == 'humidity':
            points = [
                (Thermohygrometer.replace_comma(calibration_certificate.humidity_indication_point_1), Thermohygrometer.replace_comma(calibration_certificate.humidity_correction_1)),
                (Thermohygrometer.replace_comma(calibration_certificate.humidity_indication_point_2), Thermohygrometer.replace_comma(calibration_certificate.humidity_correction_2)),
                (Thermohygrometer.replace_comma(calibration_certificate.humidity_indication_point_3), Thermohygrometer.replace_comma(calibration_certificate.humidity_correction_3)),
            ]
        else:
            raise ValueError("measurement_type must be 'temperature' or 'humidity'")
        
        # Sort points by measurement value
        points.sort(key=lambda x: x[0])
        
        # If measured value is outside the calibration range, use the nearest point
        if measured_value <= points[0][0]:
            return points[0][1]
        elif measured_value >= points[-1][0]:
            return points[-1][1]
        
        # Find the two nearest points for interpolation
        for i in range(len(points) - 1):
            if points[i][0] <= measured_value < points[i+1][0]:
                lower_point, upper_point = points[i], points[i+1]
                break
        
        # Perform linear interpolation
        slope = (upper_point[1] - lower_point[1]) / (upper_point[0] - lower_point[0])
        correction = lower_point[1] + slope * (measured_value - lower_point[0])
        # print(f"""
        #     thermohygrometer.thermohygrometer.get_correction\n  
        #     Upper: {upper_point}, Lower: {lower_point}, Slope: {slope}, Correction: {correction}
        #     """)
        return correction

    # Usage example
    def apply_correction(self, calibration_certificate, measurement_type, measured_value):
        correction = self.get_correction(calibration_certificate, measurement_type, measured_value)
        corrected_value = round(measured_value - correction, 2)
        return corrected_value

    @staticmethod
    def replace_comma(value):
        if type(value) is str:
            if ',' in value:
                return float(value.replace(',','.'))
        else:
            return value
            