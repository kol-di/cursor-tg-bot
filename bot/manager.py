from telethon import TelegramClient
import asyncio
import threading
from pathlib import Path

from bot.utils.singleton import Singleton 
from bot.access import UserAccess


class BotManager(metaclass=Singleton):
    def __init__(self, api_id, api_hash, bot_token):
        import __main__
        session_path = str(Path(__main__.__file__).parent / 'bot.session')
        self.bot = TelegramClient(session_path, api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)
        self.thread_exit_signal = threading.Event()

        self._loop = asyncio.get_event_loop()
    
    def run_until_complete(self):
        # imports inside to prevemt circular import
        from bot.scenarios.reporter.watcher import spawn_document_handlers
        from bot.scenarios.new_users import enable_event_handler
        from bot.scenarios.subscribe import (
            all_subscriptions_event_handler, 
            one_subscription_event_handler, 
            choose_subscription_event_handler)

        # register event handlers
        for handler in [
                enable_event_handler, 
                all_subscriptions_event_handler, 
                one_subscription_event_handler, 
                choose_subscription_event_handler]:
            self.bot.add_event_handler(handler)

        # create document handler threads
        spawn_document_handlers()

        # enable periodic user_access dump
        self._loop.create_task(
            self.periodic_exec(UserAccess().dump_all))

        # main loop
        try:
            self._loop.run_until_complete(self.bot.disconnected)
        except (KeyboardInterrupt, SystemExit):
            print("Exiting")
            self.thread_exit_signal.set()
            UserAccess().dump_all()
        finally:
            self.bot.disconnect()

    @staticmethod
    async def periodic_exec(func, timeout=60*60):
        while True:
            await asyncio.sleep(timeout)
            func()
