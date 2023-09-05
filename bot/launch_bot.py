from telethon import TelegramClient
import configparser
import pathlib

from .access import UserAccess


# read sensible data
config_path = pathlib.Path(__file__).parent / "config.ini"
config = configparser.ConfigParser()
config.read(config_path)

api_id = config['API']['id']
api_hash = config['API']['hash']
bot_token = config['BOT']['token']

ACCESS_CODE = config['ACCESS']['code']

# create bot
bot = TelegramClient('bot', api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)

# object for managing accees rights. 
# Not recommended to create multiple instances, please reuse this object
user_access = UserAccess()


# associate all event handlers with bot
from .scenarios.contracts_no_items_report.interactions import *
from .scenarios.new_users import *
from .scenarios.subscribe import *


bot.start()
bot.run_until_disconnected()




