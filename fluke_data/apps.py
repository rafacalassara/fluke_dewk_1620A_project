from django.apps import AppConfig
import asyncio
import threading

class FlukeDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fluke_data'

    # def ready(self):
    #     # Avoid running this code in manage.py migrate
    #     import sys
    #     if 'runserver' not in sys.argv:
    #         return

    #     from .connection_manager import InstrumentConnectionManager

    #     def run_async_loop():
    #         print('Initialized READY')
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)
    #         loop.run_until_complete(InstrumentConnectionManager.connect_all_instruments())

    #     # Start the connection manager in a separate thread
    #     thread = threading.Thread(target=run_async_loop, daemon=True)
    #     thread.start()