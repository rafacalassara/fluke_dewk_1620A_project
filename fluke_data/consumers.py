# fluke_data/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from .visa_communication import Instrument

class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.instrument = Instrument('10.140.27.21')  # Replace with your instrument's IP address

        while True:
            data = self.instrument.get_data()
            await self.send(text_data=json.dumps({'data': data}))
            await asyncio.sleep(1)

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        pass
