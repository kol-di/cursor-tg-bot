from telethon import events

from bot.launch_bot import bot
from bot.launch_bot import user_access
from bot.access import User
from bot.launch_bot import ACCESS_CODE


@bot.on(events.NewMessage(pattern='/enable'))
async def my_event_handler(event):
    sender = await event.get_sender()
    user = User(sender.username)

    if not user in user_access.get_authorized_users():
        user_access.add_unauthorized(user)

        async with bot.conversation(sender, timeout=60, replies_are_responses=True) as conv:
            await conv.send_message('Что бы получать рассылку введите кодовое слово')
            code_response = await conv.get_response()
            code = code_response.raw_text
            if code == ACCESS_CODE:
                user_access.add_authorized(user)
                await conv.send_message('Активация успешна')
            else:
                await conv.send_message('Неверное кодовое слово')
    else:
        await event.reply('Вы уже подключены к рассылке')