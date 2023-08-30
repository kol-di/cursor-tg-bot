from telethon import events

from bot.launch_bot import bot



@bot.on(events.NewMessage)
async def my_event_handler(event):
    if 'hello' in event.raw_text:
        await event.reply('hi!')