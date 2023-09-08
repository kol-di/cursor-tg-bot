from telethon import events

from bot.manager import BotManager
from bot.access import User, UserAccess
from config import ACCESS_CODE

bot = BotManager().bot
user_access = UserAccess()


@events.register(events.NewMessage(pattern='/enable'))
async def enable_event_handler(event):
    sender = await event.get_sender()
    user = User(sender.username)

    if not user in user_access._users:
        user_access.add_unauthorized(user)

        async with bot.conversation(sender, timeout=60, replies_are_responses=True) as conv:
            await conv.send_message('Что бы получать рассылку введите кодовое слово')
            code_response = await conv.get_response()
            code = code_response.raw_text
            if code == ACCESS_CODE:
                user_access.add_authorized(user)
                await conv.send_message('Активация успешна')
                print(f"New authenticated user: {user.nickname}")
            else:
                await conv.send_message('Неверное кодовое слово')
    else:
        await event.reply('Вы уже подключены к рассылке')


__all__ = ['enable_event_handler']