from telethon import events, Button
import re
import warnings

from bot.launch_bot import bot, user_access
from bot.access import User
from bot.access import \
    _RECIPIENT_RIGHT_PREFIX, \
    REC_CONTRACTS_NO_ITEMS, \
    REC_ODNOPOZ_ODNOLOT_LS_NO_CONTRACT_223


def user_callback(user_id):
    return events.CallbackQuery(chats=user_id)


@bot.on(events.CallbackQuery(data = re.compile(_RECIPIENT_RIGHT_PREFIX)))
async def choose_subscriptio_event_handler(event):
    sender = await event.get_sender()
    user = User(sender.username)
    access_right = await event.get_data.decode()  # data comes in form of bytes and should be converted

    if user in user_access.get_authorized_users():

        if user_access.is_granted(user, access_right):
            async with bot.conversation(sender, timeout=60, replies_are_responses=True) as conv:

                await conv.send_message(
                    message="Вы уже подписаны на эту рассылку. Желаете отменить?", 
                    buttons=[
                        Button.inline('Да', data='y'), Button.inline('Нет', data='n')
                    ])
                
                del_callback = await conv.wait_event(user_callback(sender))
                match del_callback.data.decode():
                    case 'y':
                        user_access.remove_acces(user, access_right)
                        await del_callback.delete()
                        await conv.send_message('Рассылка отменена')
                        conv.cancel()
                    case 'n':
                        await del_callback.delete()
                        conv.cancel()
                    case _:
                        warnings.warn("Invalid parameter passed through inline query")

        else:
            user_access.grant_acces(user, access_right)
            await bot.send_message(
                sender, 
                "Теперь вы подписаны на рассылку")


@bot.on(events.NewMessage(pattern='/add_remove_subscription'))
async def choose_subscriptio_event_handler(event):
    sender = await event.get_sender()
    user = User(sender.username)
    if user in user_access.get_authorized_users():
        await bot.send_message(
            sender, 
            message="Выберите рассылку", 
            buttons=[
                [Button.inline('Все', data='all')], 

                [Button.inline('Контракты без позиций с неверными статусами', data=REC_CONTRACTS_NO_ITEMS),  
                 Button.inline('223 однопозы однолоты ЛС без контрактов в БД', data=REC_ODNOPOZ_ODNOLOT_LS_NO_CONTRACT_223)]
            ])
