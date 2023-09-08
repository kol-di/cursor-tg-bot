from bot.manager import BotManager
from bot.access import UserAccess
from config import conf


def create_user_access():
    user_access = UserAccess()
    user_access.recover_from_dump()
    return user_access

def create_bot_manager(api_id, api_hash, bot_token):
    return BotManager(api_id, api_hash, bot_token)


if __name__ == '__main__':
    print('Starting execution')
    create_user_access()
    bot_manager = create_bot_manager(
        conf['API']['id'], 
        conf['API']['hash'], 
        conf['BOT']['token']
    )
    print('Config read')
    bot_manager.run_until_complete()

