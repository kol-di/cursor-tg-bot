from bot.manager import BotManager
from bot.access import UserAccess
from config import conf
from db.connection import ServerConnection


def create_user_access():
    user_access = UserAccess()
    user_access.recover_from_dump()
    return user_access

def create_bot_manager(api_id, api_hash, bot_token):
    return BotManager(api_id, api_hash, bot_token)

def create_server_connection(address, database, username, password):
    connection_string = \
        f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={address};DATABASE={database};UID={username};PWD={password};Encrypt=no'
    return ServerConnection(connection_string)


if __name__ == '__main__':
    print('Starting execution')
    user_access = create_user_access()
    create_server_connection(
        conf['SERVER']['address'], 
        conf['SERVER']['database'], 
        conf['SERVER']['username'], 
        conf['SERVER']['password']
    )
    bot_manager = create_bot_manager(
        conf['API']['id'], 
        conf['API']['hash'], 
        conf['BOT']['token']
    )
    print('Config read')
    bot_manager.run_until_complete()

