# fluke_data/consumers.py

import asyncio
import json
from datetime import datetime, timedelta

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import *
from .visa_communication import Instrument


class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.initialize_consumer()
        if self.instrument and self.instrument.instrument:
            await self.add_to_group()
            await self.accept()
            await sync_to_async(self.set_calibration_info)()
            await self.send_connecting_message()
            await sync_to_async(self.update_connection_status)(True)
            asyncio.create_task(self.send_data_loop())
        else:
            await self.send_failure_message()
            await self.close()

    async def disconnect(self, close_code):
        self.running = False
        await self.disconnect_instrument()
        await self.remove_from_group()
        await sync_to_async(self.update_connection_status)(False)

    async def receive(self, text_data):
        message = json.loads(text_data)
        if message.get('command') == 'disconnect':
            await self.close()

    async def send_data_loop(self):
        self.last_saved_time = {}  # Track last saved time for each sensor
        while self.running:
            try:
                # Check if we have a properly initialized instrument and sensors
                if not hasattr(self, 'instrument') or not self.instrument:
                    raise Exception("Instrument not properly initialized")
                    
                if not self.sensors:
                    # Try to fetch sensors again if list is empty
                    self.sensors = await sync_to_async(list)(SensorModel.objects.filter(instrument=self.thermo))
                    if not self.sensors:
                        raise Exception("No sensors found for this thermohygrometer")
                
                # Get data from all channels
                data_all_channels = await sync_to_async(self.instrument.get_live_data_all_channels)()
                if data_all_channels:
                    # Process and broadcast data for each sensor/channel
                    for sensor in self.sensors:
                        channel = sensor.channel
                        if channel in data_all_channels:
                            channel_data = data_all_channels[channel]
                            processed_data = await sync_to_async(self.process_measurement_data_from_instrument)(
                                channel_data, sensor
                            )
                            await self.broadcast_data(processed_data, sensor)
                            await self.check_and_save_data(processed_data, sensor)
            except Exception as e:
                await self.broadcast_error(f'consumer.send_data_loop: {str(e)}')
            await asyncio.sleep(5)

    async def thermo_data(self, event):
        if 'error' in event:
            await self.send(text_data=json.dumps({'error': event['error']}))
        else:
            await self.send(text_data=json.dumps({'data': event['data']}))

    # Helper Methods
    async def initialize_consumer(self):
        self.thermohygrometer_id = self.scope['url_route']['kwargs']['thermohygrometer_id']
        self.sensors = []  # Initialize sensors as an empty list to prevent attribute errors
        
        try: 
            self.thermo = await sync_to_async(self.get_thermohygrometer)(self.thermohygrometer_id)
            self.instrument = await sync_to_async(self.get_instrument_from_db)()
            self.sensors = await sync_to_async(list)(SensorModel.objects.filter(instrument=self.thermo))
        except Exception as e:
            await sync_to_async(self.update_connection_status)(False)
            print(f"Error initializing consumer: {str(e)}")
        
        self.group_name = f"thermohygrometer_{self.instrument.GROUP_NAME}" if hasattr(self, 'instrument') else f"thermohygrometer_error"
        self.listener_group_name = f'thermo_{self.thermohygrometer_id}'
        self.running = True

    def set_calibration_info(self):
        try:
            self.calibration_certificate = CalibrationCertificateModel.objects.get(id=self.thermo.calibration_certificate.id)
        except AttributeError:
            self.calibration_certificate = None

    async def add_to_group(self):
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def remove_from_group(self):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_connecting_message(self):
        await self.send(text_data=json.dumps({'message': 'Connecting...'}))

    async def send_failure_message(self):
        await self.send(text_data=json.dumps({'message': 'Failed to connect'}))

    async def broadcast_data(self, data, sensor):
        # Send data to the group associated with this consumer
        info = {
            'sn': self.instrument.SN,
            'pn': self.instrument.PN,
            'instrument_name': self.instrument.INSTRUMENT_NAME,
            'group_name': self.instrument.GROUP_NAME,
            'sensor_id': sensor.id,
            'sensor_name': sensor.sensor_name,
            'location': sensor.location,
            'channel': sensor.channel,
            'min_temperature': sensor.min_temperature or self.thermo.min_temperature,
            'max_temperature': sensor.max_temperature or self.thermo.max_temperature,
            'min_humidity': sensor.min_humidity or self.thermo.min_humidity,
            'max_humidity': sensor.max_humidity or self.thermo.max_humidity,
        }

        data.setdefault('thermo_info', info)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'thermo_data',
                'data': data,
            }
        )

        # Forward the data to the listener_consumer_group
        await self.channel_layer.group_send(
            self.listener_group_name,
            {
                "type": "send_data_to_listeners",
                "message": json.dumps(data)
            }
        )

    async def broadcast_error(self, error):
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'thermo_data',
                'error': error,
            }
        )

    async def disconnect_instrument(self):
        if hasattr(self.instrument, 'disconnect'):
            await sync_to_async(self.instrument.disconnect)()

    def get_thermohygrometer(self, thermohygrometer_id):
        return ThermohygrometerModel.objects.get(id=thermohygrometer_id)

    def get_instrument_from_db(self):
        return Instrument(self.thermo.ip_address)

    async def check_and_save_data(self, data, sensor):
        current_time = datetime.strptime(data['date'], '%Y/%m/%d %H:%M:%S')
        time_interval = self.thermo.time_interval_to_save_measures
        
        if sensor.id not in self.last_saved_time or current_time >= self.last_saved_time[sensor.id] + timedelta(minutes=time_interval):
            await sync_to_async(self.save_data_to_db)(data, sensor)
            self.last_saved_time[sensor.id] = current_time

    def save_data_to_db(self, data, sensor):
        if not self.calibration_certificate:
            data['corrected_temperature'] = None
            data['corrected_humidity'] = None

        MeasuresModel.objects.create(
            instrument=self.thermo,
            sensor=sensor,
            temperature=data['temperature'],
            corrected_temperature=data['corrected_temperature'],
            humidity=data['humidity'],
            corrected_humidity=data['corrected_humidity'],
            date=datetime.strptime(data['date'], '%Y/%m/%d %H:%M:%S')
        )

    def update_connection_status(self, status):
        ThermohygrometerModel.objects.filter(id=self.thermohygrometer_id).update(is_connected=status)

    def correct_measures(self, data, sensor):
        if self.calibration_certificate:    
            data['corrected_temperature'] = self.instrument.apply_correction(self.calibration_certificate, 'temperature', data['temperature'])
            data['corrected_humidity'] = self.instrument.apply_correction(self.calibration_certificate, 'humidity', data['humidity'])
        else:
            data['corrected_temperature'] = 'No Calibration Certificate'
            data['corrected_humidity'] = 'No Calibration Certificate'
            
        return data

    def define_measures_style_based_on_limits(self, data, sensor):
        min_temp = sensor.min_temperature or self.thermo.min_temperature
        max_temp = sensor.max_temperature or self.thermo.max_temperature
        min_humidity = sensor.min_humidity or self.thermo.min_humidity
        max_humidity = sensor.max_humidity or self.thermo.max_humidity
        
        data['temperature_style'] = 'black'
        data['humidity_style'] = 'black'
        data['corrected_temperature_style'] = 'black'
        data['corrected_humidity_style'] = 'black'
        
        if data['temperature'] < min_temp or data['temperature'] > max_temp:
            data['temperature_style'] = 'red'
        if data['humidity'] < min_humidity or data['humidity'] > max_humidity:
            data['humidity_style'] = 'red'

        if self.calibration_certificate:
            if data['corrected_temperature'] < min_temp or data['corrected_temperature'] > max_temp:
                data['corrected_temperature_style'] = 'red'
            if data['corrected_humidity'] < min_humidity or data['corrected_humidity'] > max_humidity:
                data['corrected_humidity_style'] = 'red'
        else:
            data['corrected_temperature_style'] = 'red'
            data['corrected_humidity_style'] = 'red'

        return data

    def process_measurement_data_from_instrument(self, data, sensor):
        # Add sensor information to the data
        data['sensor_id'] = sensor.id
        data['sensor_name'] = sensor.sensor_name
        data['location'] = sensor.location
        data['channel'] = sensor.channel
        
        data = self.correct_measures(data, sensor)
        data = self.define_measures_style_based_on_limits(data, sensor)

        return data


class ListenerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thermohygrometer_id = self.scope['url_route']['kwargs']['thermohygrometer_id']
        thermo = await sync_to_async(self.get_thermohygrometer)(self.thermohygrometer_id)
        self.listener_group_name = f'thermo_{thermo.id}'

        await self.channel_layer.group_add(self.listener_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.listener_group_name, self.channel_name)

    async def send_data_to_listeners(self, event):
        message = event['message']
        await self.send(text_data=message)

    def get_thermohygrometer(self, thermohygrometer_id):
        return ThermohygrometerModel.objects.get(id=thermohygrometer_id)


class ThermohygrometerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thermohygrometer_id = self.scope['url_route']['kwargs']['thermohygrometer_id']
        thermo = await sync_to_async(self.get_thermohygrometer)(self.thermohygrometer_id)
        self.listener_group_name = f'thermo_{thermo.id}'

        await self.channel_layer.group_add(self.listener_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.listener_group_name, self.channel_name)

    async def send_data_to_listeners(self, event):
        message = event['message']
        await self.send(text_data=message)

    async def send_data(self):
        sensors = await sync_to_async(list)(
            SensorModel.objects.filter(instrument=self.thermo)
        )
        
        try:
            instrument = Instrument(ip_address=self.thermo.ip_address)
            await sync_to_async(instrument.connect)()
            
            data_all_channels = await sync_to_async(instrument.get_live_data_all_channels)()
            
            if not data_all_channels:
                await self.send(text_data=json.dumps({
                    'error': 'Error reading data from thermohygrometer'
                }))
                return
                
            for sensor in sensors:
                channel_data = data_all_channels.get(sensor.channel)
                if not channel_data:
                    continue
                
                temperature = channel_data.get('temperature')
                humidity = channel_data.get('humidity')
                date = channel_data.get('date')
                
                corrected_temperature = temperature
                corrected_humidity = humidity
                
                if self.thermo.calibration_certificate:
                    corrected_temperature = await sync_to_async(instrument.apply_correction)(
                        self.thermo.calibration_certificate, 'temperature', temperature
                    )
                    corrected_humidity = await sync_to_async(instrument.apply_correction)(
                        self.thermo.calibration_certificate, 'humidity', humidity
                    )
                
                min_temp = sensor.min_temperature
                max_temp = sensor.max_temperature
                min_humidity = sensor.min_humidity
                max_humidity = sensor.max_humidity
                
                if min_temp is None:
                    min_temp = self.thermo.min_temperature
                if max_temp is None:
                    max_temp = self.thermo.max_temperature
                if min_humidity is None:
                    min_humidity = self.thermo.min_humidity
                if max_humidity is None:
                    max_humidity = self.thermo.max_humidity
                
                temperature_style = 'black'
                humidity_style = 'black'
                corrected_temperature_style = 'black'
                corrected_humidity_style = 'black'
                
                if temperature < min_temp or temperature > max_temp:
                    temperature_style = 'red'
                if humidity < min_humidity or humidity > max_humidity:
                    humidity_style = 'red'

                if self.thermo.calibration_certificate:
                    if corrected_temperature < min_temp or corrected_temperature > max_temp:
                        corrected_temperature_style = 'red'
                    if corrected_humidity < min_humidity or corrected_humidity > max_humidity:
                        corrected_humidity_style = 'red'
                else:
                    corrected_temperature_style = 'red'
                    corrected_humidity_style = 'red'
                
                await self.send(text_data=json.dumps({
                    'data': {
                        'sensor_id': sensor.id,
                        'sensor_name': sensor.sensor_name,
                        'location': sensor.location,
                        'channel': sensor.channel,
                        'temperature': temperature,
                        'humidity': humidity,
                        'corrected_temperature': corrected_temperature,
                        'corrected_humidity': corrected_humidity,
                        'date': date,
                        'temperature_style': temperature_style,
                        'corrected_temperature_style': corrected_temperature_style,
                        'humidity_style': humidity_style,
                        'corrected_humidity_style': corrected_humidity_style,
                        'thermo_info': {
                            'id': self.thermo.id,
                            'instrument_name': self.thermo.instrument_name,
                            'min_temperature': min_temp,
                            'max_temperature': max_temp,
                            'min_humidity': min_humidity,
                            'max_humidity': max_humidity,
                        }
                    }
                }))
        except Exception as e:
            self.log_error(f"Error occurred: {str(e)}")

    def get_thermohygrometer(self, thermohygrometer_id):
        return ThermohygrometerModel.objects.get(id=thermohygrometer_id)