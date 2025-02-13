import asyncio

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import ThermohygrometerModel
from .visa_communication import Instrument


class InstrumentConnectionManager:
    @staticmethod
    async def connect_to_instrument(thermo):
        try:
            instrument = await sync_to_async(Instrument)(thermo.ip_address)
            if instrument.instrument:
                await sync_to_async(thermo.save)()
                await sync_to_async(ThermohygrometerModel.objects.filter(id=thermo.id).update)(
                    is_connected=True,
                    last_connection_attempt=timezone.now()
                )
                channel_layer = get_channel_layer()
                await channel_layer.group_send(
                    f"thermohygrometer_{thermo.group_name}",
                    {"type": "instrument_connected", "thermohygrometer_id": thermo.id}
                )
                print(f"InstrumentConnectionManager.connect_to_instrument: Connected to {thermo.instrument_name}")
                asyncio.create_task(InstrumentConnectionManager.send_data_loop(instrument, thermo))
                return instrument
        except Exception as e:
            print(f"connection_manager.connect_to_instrument: Error connecting to {thermo.instrument_name}: {str(e)}")
        return None

    @staticmethod
    async def send_data_loop(instrument, thermo):
        channel_layer = get_channel_layer()
        while True:
            try:
                data = await sync_to_async(instrument.get_data)()
                if data:
                    await channel_layer.group_send(
                        f'thermo_{thermo.id}',
                        {
                            "type": "send_data_to_listeners",
                            "message": data
                        }
                    )
            except Exception as e:
                print(f"connection_manager.send_data_loop: Error getting data from {thermo.instrument_name}: {str(e)}")
                break
            await asyncio.sleep(1)  # Adjust the interval as needed

    @staticmethod
    async def connect_all_instruments():
        from pyvisa import errors as visa_errors
        while True:
            thermos = await sync_to_async(list)(ThermohygrometerModel.objects.all())
            
            for thermo in thermos:
                try:
                    await InstrumentConnectionManager.connect_to_instrument(thermo)
                except visa_errors.VisaIOError:
                    print(f'{thermo} already connected.')
            await asyncio.sleep(60)  # Wait for 1 minute before the next connection attempt

