from telethon import events

import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pathlib import Path
from threading import Thread




class NewReportHandler:
    def __init__(self):
        self._handler = PatternMatchingEventHandler(
            patterns=["*"], 
            ignore_patterns=None,
            ignore_directories=False,
            case_sensitive=False
        )
        self._handler.on_created = self._on_created

        self._report_dir = None
        self._observer = None


    @property
    def report_dir(self):
        return self._report_dir
    
    @report_dir.setter
    def report_dir(self, input_path):
        path = Path(input_path)
        if path.exists():
            pass
        else:
            path = Path(__file__).parent / input_path
            if path.exists():
                pass
            else:
                raise Exception("Invalid path")
            
        if path.is_dir():
            self._report_dir = path
        else:
            raise Exception("Path should be a directory")
        

    def create_observer(self, path=None):
        if path is None:
            path = self.report_dir
        if path is None:
            raise Exception("No report directory provided")
        
        self._observer = Observer()
        self._observer.schedule(self._handler, path, recursive=True)


    def run_observer(self, upd_time=60*30):
        self._observer.start()
        try:
            while True:
                time.sleep(upd_time)
        except KeyboardInterrupt:
            self._observer.stop()
            self._observer.join()
        

    def _on_created(self, event):
        print(f"hey, {event.src_path} has been created!")





handler = NewReportHandler()
handler.report_dir = "reports"
handler.create_observer()

watchdog_thread = Thread(target=handler.run_observer, name='Watchdog', daemon=True, args=(60*30,))
watchdog_thread.start()
# handler.run_observer(upd_time=1)





from bot.launch_bot import bot

@bot.on(events.NewMessage)
async def my_event_handler(event):
    if 'hello' in event.raw_text:
        await event.reply('hi!')






