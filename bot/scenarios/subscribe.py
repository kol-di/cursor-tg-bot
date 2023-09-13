from telethon import events, Button
import re
import warnings

from bot.manager import BotManager 
from db.connection import ServerConnection
from bot.access import _RECIPIENT_RIGHT_PREFIX_REP, _RECIPIENT_RIGHT_PREFIX_CAT

bot = BotManager().bot
conn = ServerConnection()


class InvalidInlineQueryParamWarning(Warning):
    pass


def user_callback(user_id):
    return events.CallbackQuery(chats=user_id)


@events.register(events.CallbackQuery(pattern='all'))
async def all_subscriptions_event_handler(event):
    sender = await event.get_sender()
    username = sender.username

    async with bot.conversation(sender, timeout=60, exclusive=False, replies_are_responses=True) as conv:
        ask_msg = await conv.send_message(
            message="Что вы хотите сделать?", 
            buttons=[
                Button.inline('Подписаться на все', data='s'), Button.inline('Отписаться от всего', data='u')
            ])
        
        all_callback = await conv.wait_event(user_callback(sender))
        match all_callback.data.decode():
            case 'u':
                conn.remove_all(username)

                await all_callback.delete()
                await conv.send_message("Вы отписались от всех рассылок")
                print(f'User {username} unsubscribed from all')
            case 's':
                conn.grant_all(username)

                await all_callback.delete()
                await conv.send_message("Вы подписалсиь на все рассылки")
                print(f'User {username} subscribed to all')
            case _ as var:
                warnings.warn(f"Invalid parameter {var}", InvalidInlineQueryParamWarning)
                await bot.delete_messages(entity=sender, message_ids=ask_msg.id)
        conv.cancel()


@events.register(events.CallbackQuery(data = re.compile(_RECIPIENT_RIGHT_PREFIX_REP)))
async def one_subscription_event_handler_rep(event):
    sender = await event.get_sender()
    username = sender.username

    access_right = event.data.decode()  # data comes in form of bytes and should be converted

    if conn.is_granted(username, report=access_right):
        async with bot.conversation(sender, timeout=60, exclusive=False, replies_are_responses=True) as conv:

            ask_msg = await conv.send_message(
                message="Вы уже подписаны на эту рассылку. Желаете отменить?", 
                buttons=[
                    Button.inline('Да', data='y'), Button.inline('Нет', data='n')
                ])
            
            del_callback = await conv.wait_event(user_callback(sender))
            match del_callback.data.decode():
                case 'y':
                    conn.remove_access(username, report=access_right)
                    await del_callback.delete()
                    await conv.send_message('Рассылка отменена')
                    print(f'User {username} unsubscribed from {access_right}')
                case 'n':
                    await del_callback.delete()
                case _ as var:
                    warnings.warn(f"Invalid parameter {var}", InvalidInlineQueryParamWarning)
                    await bot.delete_messages(entity=sender, message_ids=ask_msg.id)
            conv.cancel()

    else:
        conn.grant_access(username, report=access_right)
        await bot.send_message(
            sender, 
            "Теперь вы подписаны на рассылку")
        print(f'User {username} subscribed to {access_right}')


@events.register(events.CallbackQuery(data = re.compile(_RECIPIENT_RIGHT_PREFIX_CAT)))
async def one_subscription_event_handler_cat(event):
    sender = await event.get_sender()
    username = sender.username

    access_right = event.data.decode()  # data comes in form of bytes and should be converted

    if conn.is_granted(username, report_category=access_right):
        async with bot.conversation(sender, timeout=60, exclusive=False, replies_are_responses=True) as conv:

            ask_msg = await conv.send_message(
                message="Вы уже подписаны на эту рассылку. Желаете отменить?", 
                buttons=[
                    Button.inline('Да', data='y'), Button.inline('Нет', data='n')
                ])
            
            del_callback = await conv.wait_event(user_callback(sender))
            match del_callback.data.decode():
                case 'y':
                    conn.remove_access(username, report_category=access_right)
                    await del_callback.delete()
                    await conv.send_message('Рассылка отменена')
                    print(f'User {username} unsubscribed from {access_right}')
                case 'n':
                    await del_callback.delete()
                case _ as var:
                    warnings.warn(f"Invalid parameter {var}", InvalidInlineQueryParamWarning)
                    await bot.delete_messages(entity=sender, message_ids=ask_msg.id)
            conv.cancel()

    else:
        conn.grant_access(username, report_category=access_right)
        await bot.send_message(
            sender, 
            "Теперь вы подписаны на рассылку")
        print(f'User {username} subscribed to {access_right}')


def _create_buttons(buttons_in_row=2):
    btns = []
    # button to choose all
    btns.append([Button.inline('Все', data='all')])

    # buttons for report categories
    report_cat_btns = [Button.inline(row[1], data=row[0]) for row in 
                       conn.all_report_categories(columns=['Name', 'DisplayName'])]
    num_rows_report_cat = \
        len(report_cat_btns) // buttons_in_row + \
        int(bool(len(report_cat_btns) % buttons_in_row))
    
    for row_n in range(num_rows_report_cat):
        btns.append(report_cat_btns[row_n * buttons_in_row: (row_n + 1) * buttons_in_row])

    # buttons for reports
    report_btns = [Button.inline(row[1], data=row[0]) for row in 
                   conn.all_reports(columns=['Name', 'DisplayName'], no_category=True)]
    num_rows_report = \
        len(report_btns) // buttons_in_row + \
        int(bool(len(report_btns) % buttons_in_row))
    
    for row_n in range(num_rows_report):
        btns.append(report_btns[row_n * buttons_in_row: (row_n + 1) * buttons_in_row])
    
    return btns


@events.register(events.NewMessage(pattern='/add_remove_subscription'))
async def choose_subscription_event_handler(event):
    sender = await event.get_sender()
    username = sender.username

    if username in conn.get_authorised():
        await bot.send_message(
            sender, 
            message="Выберите рассылку", 
            buttons=_create_buttons())
        

__all__ = ['all_subscriptions_event_handler', 
       'one_subscription_event_handler_rep',
       'one_subscription_event_handler_cat', 
       'choose_subscription_event_handler']
