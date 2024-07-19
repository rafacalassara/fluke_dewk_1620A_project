# fluke_data/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from .visa_communication import Instrument
from asgiref.sync import sync_to_async

class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Use sync_to_async to instantiate Instrument
        self.instrument = await sync_to_async(Instrument)('10.140.27.21')  # Replace with your instrument's IP address

        while True:
            data = await sync_to_async(self.instrument.get_data)()
            await self.send(text_data=json.dumps({'data': data}))
            await asyncio.sleep(1)

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        pass
