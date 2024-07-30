# fluke_data/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from .visa_communication import Instrument
from asgiref.sync import sync_to_async
from .models import Thermohygrometer

class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thermohygrometer_id = self.scope['url_route']['kwargs']['thermohygrometer_id']
        self.instrument = await sync_to_async(self.get_instrument)()
        await self.accept()

        while True:
            data = await sync_to_async(self.instrument.get_data)()
            await self.send(text_data=json.dumps({'data': data}))
            await asyncio.sleep(1)

    def get_instrument(self):
        thermo = Thermohygrometer.objects.get(id=self.thermohygrometer_id)
        return Instrument(thermo.ip_address)

    async def disconnect(self, close_code):
        self.running = False
        await self.close()

    async def receive(self, text_data):
        message = json.loads(text_data)
        self.instrument.instrument.close()
        if message.get('command') == 'disconnect':
            await self.close()
