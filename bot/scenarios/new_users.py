from telethon import events

from bot.manager import BotManager
from db.connection import ServerConnection
from config import ACCESS_CODE

bot = BotManager().bot
conn = ServerConnection()


@events.register(events.NewMessage(pattern='/enable'))
async def enable_event_handler(event):
    sender = await event.get_sender()
    username = sender.username

    access_status = next(
        (entry[0] for entry in conn.all_users() if entry[1] == username), 
        None)
    
    if access_status is None or access_status == False:
        conn.add_unauthorized(username)

        async with bot.conversation(sender, timeout=60, replies_are_responses=True) as conv:
            await conv.send_message('Что бы получать рассылку введите кодовое слово')
            code_response = await conv.get_response()
            code = code_response.raw_text
            if code == ACCESS_CODE:
                conn.add_authorized(username)
                await conv.send_message('Активация успешна')
                print(f"New authenticated user: {username}")
            else:
                await conv.send_message('Неверное кодовое слово')
    else:
        await event.reply('Вы уже подключены к рассылке')


__all__ = ['enable_event_handler']