from telethon import TelegramClient
import asyncio
import threading
from pathlib import Path

from utils.singleton import Singleton 
from db.connection import ServerConnection


class BotManager(metaclass=Singleton):
    def __init__(self, api_id, api_hash, bot_token):
        import __main__
        session_path = str(Path(__main__.__file__).parent / 'bot.session')
        self.bot = TelegramClient(session_path, api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)

        self._loop = asyncio.get_event_loop()
        self._conn = ServerConnection()
    
    def run_until_complete(self):
        # imports inside to prevemt circular import
        from bot.scenarios.reporter.executor import ReportExecutor
        from bot.scenarios.new_users import enable_event_handler
        from bot.scenarios.subscribe import (
            all_subscriptions_event_handler, 
            one_subscription_event_handler_rep,
            one_subscription_event_handler_cat, 
            choose_subscription_event_handler)

        # register event handlers
        for handler in [
                enable_event_handler, 
                all_subscriptions_event_handler, 
                one_subscription_event_handler_rep,
                one_subscription_event_handler_cat, 
                choose_subscription_event_handler]:
            self.bot.add_event_handler(handler)

        # enable report executors
        for ex in ReportExecutor.create_executors(self.bot, self._conn):
            self._loop.create_task(ex.run_task())

        # main loop
        try:
            self._loop.run_until_complete(self.bot.disconnected)
        except (KeyboardInterrupt, SystemExit):
            print("Exiting")
            self._conn.close()
        finally:
            self.bot.disconnect()
