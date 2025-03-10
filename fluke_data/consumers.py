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
        self.running = True

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
        
        # Create a unique group name for this specific sensor
        sensor_group_name = f'thermo_{self.thermohygrometer_id}_sensor_{sensor.id}'

        # Forward the data to the specific sensor group for listeners
        await self.channel_layer.group_send(
            sensor_group_name,
            {
                "type": "send_data_to_listeners",
                "message": json.dumps(data)
            }
        )
        
        # Also send to the general thermohygrometer group for listeners who want all sensors
        general_group_name = f'thermo_{self.thermohygrometer_id}'
        await self.channel_layer.group_send(
            general_group_name,
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
        # Check if the sensor has a calibration certificate
        if hasattr(sensor, 'calibration_certificate') and sensor.calibration_certificate:
            data['corrected_temperature'] = self.instrument.apply_correction(
                sensor.calibration_certificate, 'temperature', data['temperature']
            )
            data['corrected_humidity'] = self.instrument.apply_correction(
                sensor.calibration_certificate, 'humidity', data['humidity']
            )
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

        has_calibration = hasattr(sensor, 'calibration_certificate') and sensor.calibration_certificate
        if has_calibration:
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
        self.sensor_id = self.scope['url_route']['kwargs'].get('sensor_id', None)
        
        # Get the thermohygrometer and store it in an instance variable
        self.thermo = await sync_to_async(self.get_thermohygrometer)(self.thermohygrometer_id)
        
        # If a sensor_id is provided, subscribe to that specific sensor's group
        if self.sensor_id:
            self.listener_group_name = f'thermo_{self.thermohygrometer_id}_sensor_{self.sensor_id}'
        else:
            # Otherwise, subscribe to all data for this thermohygrometer
            self.listener_group_name = f'thermo_{self.thermohygrometer_id}'

        await self.channel_layer.group_add(self.listener_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.listener_group_name, self.channel_name)

    async def send_data_to_listeners(self, event):
        message = event['message']
        await self.send(text_data=message)

    def get_thermohygrometer(self, thermohygrometer_id):
        thermo = ThermohygrometerModel.objects.get(id=thermohygrometer_id)
        
        # Store sensors as an instance variable if needed
        if hasattr(self, 'thermo'):
            self.sensors = SensorModel.objects.filter(instrument=thermo)
            
        return thermo