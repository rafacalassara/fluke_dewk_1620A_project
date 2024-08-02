import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from .visa_communication import Instrument
from asgiref.sync import sync_to_async
from .models import ThermohygrometerModel

class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thermohygrometer_id = self.scope['url_route']['kwargs']['thermohygrometer_id']
        self.instrument = await sync_to_async(self.get_instrument)()
        self.group_name = f"thermo_{self.thermohygrometer_id}"
        self.running = True

        if self.instrument.instrument:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            await self.send(text_data=json.dumps({'message': 'Connecting...'}))
            asyncio.create_task(self.send_data_loop())
        else:
            await self.send(text_data=json.dumps({'message': 'Failed to connect'}))
            await self.close()

    async def disconnect(self, close_code):
        self.running = False
        if hasattr(self.instrument, 'disconnect'):
            await sync_to_async(self.instrument.disconnect)()
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        message = json.loads(text_data)
        if message.get('command') == 'disconnect':
            await self.close()

    async def send_data_loop(self):
        while self.running:
            try:
                data = await sync_to_async(self.instrument.get_data)()
                if data:
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'thermo_data',
                            'data': data,
                        }
                    )
            except Exception as e:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'thermo_data',
                        'error': str(e),
                    }
                )
            await asyncio.sleep(1)

    async def thermo_data(self, event):
        data = event.get('data', {})
        error = event.get('error', None)
        if error:
            await self.send(text_data=json.dumps({'error': error}))
        else:
            await self.send(text_data=json.dumps({'data': data}))

    def get_instrument(self):
        thermo = ThermohygrometerModel.objects.get(id=self.thermohygrometer_id)
        instrument = Instrument(thermo.ip_address)
        return instrument
