from telethon import TelegramClient
import configparser
import pathlib


# read sensible data
config_path = pathlib.Path(__file__).parent / "tg_credentials.conf"
config = configparser.ConfigParser()
config.read(config_path)

api_id = config['API']['id']
api_hash = config['API']['hash']
bot_token = config['BOT']['token']

# create bot
bot = TelegramClient('bot', api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)

# associate all event handlers with bot
from .scenarios.contracts_no_items_report.interactions import *

bot.start()
bot.run_until_disconnected()




