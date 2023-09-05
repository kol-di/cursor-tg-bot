from telethon import events, Button
import re
import warnings

from bot.launch_bot import bot, user_access
from bot.access import User
from bot.access import \
    _RECIPIENT_RIGHT_PREFIX, \
    REC_CONTRACTS_NO_ITEMS, \
    REC_ODNOPOZ_ODNOLOT_LS_NO_CONTRACT_223


class InvalidInlineQueryParamWarning(Warning):
    pass


def user_callback(user_id):
    return events.CallbackQuery(chats=user_id)


@bot.on(events.CallbackQuery(pattern='all'))
async def all_subscriptions(event):
    sender = await event.get_sender()

    user = User(sender.username)

    if user in user_access.get_authorized_users():
        async with bot.conversation(sender, timeout=60, exclusive=False, replies_are_responses=True) as conv:
            ask_msg = await conv.send_message(
                message="Что вы хотите сделать?", 
                buttons=[
                    Button.inline('Отписаться от всего', data='u'), Button.inline('Подписаться на все', data='s')
                ])
            
            all_callback = await conv.wait_event(user_callback(sender))
            match all_callback.data.decode():
                case 'u':
                    for right_alias in user_access._alias_to_right.keys():
                        user_access.remove_acces(user, right_alias)
                        await all_callback.delete()
                        await conv.send_message("Вы отписались от всех рассылок")
                        conv.cancel()
                case 's':
                    for right_alias in user_access._alias_to_right.keys():
                        user_access.grant_acces(user, right_alias)
                        await all_callback.delete()
                        await conv.send_message("Вы подписалсиь на все рассылки")
                        conv.cancel()
                case _ as var:
                    warnings.warn(f"Invalid parameter {var}", InvalidInlineQueryParamWarning)
                    # await all_callback.delete()
                    await bot.delete_messages(entity=sender, message_ids=ask_msg.id)
                    conv.cancel()



@bot.on(events.CallbackQuery(data = re.compile(_RECIPIENT_RIGHT_PREFIX)))
async def choose_subscription_event_handler(event):
    print('I entered anyway!')
    sender = await event.get_sender()

    user = User(sender.username)
    access_right = event.data.decode()  # data comes in form of bytes and should be converted

    if user in user_access.get_authorized_users():
        print('found authorized user')

        if user_access.is_granted(user, access_right):
            async with bot.conversation(sender, timeout=60, exclusive=False, replies_are_responses=True) as conv:
                print('user already in mailing list')

                ask_msg = await conv.send_message(
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
                    case _ as var:
                        warnings.warn(f"Invalid parameter {var}", InvalidInlineQueryParamWarning)
                        # await del_callback.delete()
                        await bot.delete_messages(entity=sender, message_ids=ask_msg.id)
                        conv.cancel()

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
