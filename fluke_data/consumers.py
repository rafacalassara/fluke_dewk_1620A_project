# fluke_data/consumers.py

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
from .visa_communication import Instrument
from .models import ThermohygrometerModel, MeasuresModel

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
        self.last_saved_time = None
        while self.running:
            try:
                data = await sync_to_async(self.instrument.get_data)()
                if data:
                    await self.broadcast_data(data)
                    await self.check_and_save_data(data)
            except Exception as e:
                await self.broadcast_error(str(e))
            await asyncio.sleep(1)

    async def thermo_data(self, event):
        if 'error' in event:
            await self.send(text_data=json.dumps({'error': event['error']}))
        else:
            await self.send(text_data=json.dumps({'data': event['data']}))

    # Helper Methods
    async def initialize_consumer(self):
        self.thermohygrometer_id = self.scope['url_route']['kwargs']['thermohygrometer_id']
        self.instrument = await sync_to_async(self.get_instrument)()
        self.group_name = f"thermo_{self.thermohygrometer_id}"
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

    async def broadcast_data(self, data):
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'thermo_data',
                'data': data,
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

    def get_instrument(self):
        self.thermo = ThermohygrometerModel.objects.get(id=self.thermohygrometer_id)
        return Instrument(self.thermo.ip_address)

    async def check_and_save_data(self, data):
        current_time = datetime.strptime(data['date'], '%Y/%m/%d %H:%M:%S')
        if self.last_saved_time is None or current_time >= self.last_saved_time + timedelta(minutes=1):
            await sync_to_async(self.save_data_to_db)(data)
            self.last_saved_time = current_time

    def save_data_to_db(self, data):
        MeasuresModel.objects.create(
            instrument=self.thermo,
            temperature=data['temperature'],
            humidity=data['humidity'],
            date=datetime.strptime(data['date'], '%Y/%m/%d %H:%M:%S')
        )

    def update_connection_status(self, status):
        ThermohygrometerModel.objects.filter(id=self.thermohygrometer_id).update(is_connected=status)
