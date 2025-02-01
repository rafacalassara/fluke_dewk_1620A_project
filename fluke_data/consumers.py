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
        self.last_saved_time = None
        while self.running:
            try:
                data = await sync_to_async(self.instrument.get_data)()
                if data:
                    data = await sync_to_async(self.process_measurement_data_from_instrument)(data)
                    await self.broadcast_data(data)
                    await self.check_and_save_data(data)
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
        try: 
            self.instrument = await sync_to_async(self.get_instrument_from_db)()
        except:
            await sync_to_async(self.update_connection_status)(False)
        
        self.group_name = f"thermohygrometer_{self.instrument.GROUP_NAME}"
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

    async def broadcast_data(self, data):
        # Send data to the group associated with this consumer
        info = {
            'sn': self.instrument.SN,
            'pn': self.instrument.PN,
            'instrument_name': self.instrument.INSTRUMENT_NAME,
            'group_name': self.instrument.GROUP_NAME,
            'min_temperature': self.thermo.min_temperature,
            'max_temperature': self.thermo.max_temperature,
            'min_humidity': self.thermo.min_humidity,
            'max_humidity': self.thermo.max_humidity,
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

    def get_instrument_from_db(self):
        self.thermo = ThermohygrometerModel.objects.get(id=self.thermohygrometer_id)
        return Instrument(self.thermo.ip_address)

    async def check_and_save_data(self, data):
        current_time = datetime.strptime(data['date'], '%Y/%m/%d %H:%M:%S')
        time_interval = self.thermo.time_interval_to_save_measures
        if self.last_saved_time is None or current_time >= self.last_saved_time + timedelta(minutes=time_interval):
            await sync_to_async(self.save_data_to_db)(data)
            self.last_saved_time = current_time

    def save_data_to_db(self, data):
        MeasuresModel.objects.create(
            instrument=self.thermo,
            temperature=data['temperature'],
            corrected_temperature=data['corrected_temperature'],
            humidity=data['humidity'],
            corrected_humidity=data['corrected_humidity'],
            date=datetime.strptime(data['date'], '%Y/%m/%d %H:%M:%S')
        )

    def update_connection_status(self, status):
        ThermohygrometerModel.objects.filter(id=self.thermohygrometer_id).update(is_connected=status)

    def correct_measures(self, data):
        if self.calibration_certificate:    
            data['corrected_temperature'] = self.instrument.apply_correction(self.calibration_certificate, 'temperature', data['temperature'])
            data['corrected_humidity'] = self.instrument.apply_correction(self.calibration_certificate, 'humidity', data['humidity'])
        else:
            data['corrected_temperature'] = 'No Calibration Certificate',
            data['corrected_humidity'] = 'No Calibration Certificate'
            
        return data

    def define_measures_style_based_on_limits(self, data):
        data['temperature_style'] = 'black'
        data['humidity_style'] = 'black'
        data['corrected_temperature_style'] = 'black'
        data['corrected_humidity_style'] = 'black'
        
        if data['temperature'] < self.thermo.min_temperature or data['temperature'] > self.thermo.max_temperature:
            data['temperature_style'] = 'red'
        if data['humidity'] < self.thermo.min_humidity or data['humidity'] > self.thermo.max_humidity:
            data['humidity_style'] = 'red'

        if data['corrected_temperature'] < self.thermo.min_temperature or data['corrected_temperature'] > self.thermo.max_temperature:
            data['corrected_temperature_style'] = 'red'
        if data['corrected_humidity'] < self.thermo.min_humidity or data['corrected_humidity'] > self.thermo.max_humidity:
            data['corrected_humidity_style'] = 'red'

        return data

    def process_measurement_data_from_instrument(self, data):
        data = self.correct_measures(data)
        data = self.define_measures_style_based_on_limits(data)

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