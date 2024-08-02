# fluke_data/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from .visa_communication import Instrument
from asgiref.sync import sync_to_async
from .models import ThermohygrometerModel

class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thermohygrometer_id = self.scope['url_route']['kwargs']['thermohygrometer_id']
        self.instrument = await sync_to_async(self.get_instrument)()

        if self.instrument.instrument:
            await self.accept()
            self.running = True
            while self.running:
                try:
                    data = await sync_to_async(self.instrument.get_data)()
                    if data:
                        await self.send(text_data=json.dumps({'data': data}))
                except Exception as e:
                    await self.send(text_data=json.dumps({'error': str(e)}))
                await asyncio.sleep(1)
        else:
            await self.close()

    def get_instrument(self):
        thermo = ThermohygrometerModel.objects.get(id=self.thermohygrometer_id)
        instrument = Instrument(thermo.ip_address)
        return instrument

    async def disconnect(self, close_code):
        self.running = False
        if hasattr(self.instrument, 'disconnect'):
            await sync_to_async(self.instrument.disconnect)()
        await self.close()

    async def receive(self, text_data):
        message = json.loads(text_data)
        if message.get('command') == 'disconnect':
            await self.close()
