from telethon import TelegramClient
import configparser
import pathlib

from .access import User, UserAccess


# read sensible data
config_path = pathlib.Path(__file__).parent / "tg_credentials.conf"
config = configparser.ConfigParser()
config.read(config_path)

api_id = config['API']['id']
api_hash = config['API']['hash']
bot_token = config['BOT']['token']

# create bot
bot = TelegramClient('bot', api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)

# create list of users with bot access
access_list_path = pathlib.Path(__file__).parent / "access_list.txt"
nicknames = []
with open(access_list_path, 'r') as f:
    for line in f:
        nicknames.append(line.strip())
users = [User(nick) for nick in nicknames]

user_access = UserAccess()
user_access.add_authorized(users)
user_access.grant_acces(users, 'ContractsNoItems')
print(user_access.get_authorized_users())


# associate all event handlers with bot
from .scenarios.contracts_no_items_report.interactions import *


bot.start()
bot.run_until_disconnected()




