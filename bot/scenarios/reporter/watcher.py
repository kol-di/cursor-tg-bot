from telethon.errors.rpcerrorlist import PeerIdInvalidError, MessageTooLongError

import time
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import asyncio
from concurrent import futures

from bot.manager import BotManager
from bot.access import UserAccess
from bot.access import ReportType
from bot.utils.path_resolution import resolve
from .report_builder import ReportBuilder, REPORTS_PROPERTIES


class Handler(FileSystemEventHandler):
    def __init__(self, report_type, loop):
        super().__init__()
        self._report_type = report_type
        self._loop = loop

        self.on_created = self.__on_created

        self._bot = BotManager().bot
        self._user_access = UserAccess()


    def __on_created(self, file_event):
        print(f'Found new report: {file_event.src_path}')
        asyncio.run_coroutine_threadsafe(self.__send_reports(file_event.src_path), self._loop)


    async def __send_reports(self, file):
        report = ReportBuilder()
        report.read_data(file)
        report.cols = REPORTS_PROPERTIES[self._report_type].columns

        for user in self._user_access.get_authorized_users():
            if self._user_access.is_granted(user, self._report_type):
                asyncio.create_task(self.__send_report(user, report))


    async def __send_report(self, user, report, timeout=10, rowcount_limit=30, colcount_limit=1):
        filename_prefix = REPORTS_PROPERTIES[self._report_type].filename_prefix

        try:
            if report.size <= rowcount_limit and len(report.cols) <= colcount_limit:
                try:
                    await asyncio.wait_for(
                        self._bot.send_message(
                            user.nickname, 
                            str(report)), 
                            timeout=timeout)
                    
                except MessageTooLongError:
                    await asyncio.wait_for(
                        self._bot.send_file(
                            user.nickname, 
                            report.create_file(filename_prefix)), 
                            timeout=timeout)
            else:
                await asyncio.wait_for(
                    self._bot.send_file(
                        user.nickname, 
                        report.create_file(filename_prefix)), 
                        timeout=timeout)
                
        except PeerIdInvalidError:
            print("Unable to send message to user: {}".format(user.nickname))


class ObserverManager:
    def __init__(self, handler, report_dir):
        self._handler = handler
        self.report_dir = report_dir

        self._observer = None
        self._exit_signal = None

    @property
    def report_dir(self):
        return self._report_dir
    
    @report_dir.setter
    def report_dir(self, input_path):
        path = resolve(input_path, caller_path=__file__, dir=True)    
        self._report_dir = path
        

    def create_observer(self, path=None):
        if path is None:
            path = self.report_dir
        if path is None:
            raise Exception("No report directory provided")
        
        self._exit_signal = BotManager().thread_exit_signal
        self._observer = PollingObserver()
        self._observer.schedule(self._handler, path, recursive=True)
        print('Observer created')


    def run_observer(self):
        self._observer.start()
        while not self._exit_signal.is_set():
            time.sleep(1)

        print('Observer destroyed')
        self._observer.stop()
        self._observer.join()

class Watcher:
    """
    Runs multiple observers
    """
    def __init__(self, observers):
        self._observers = observers

    def start_all(self):
        futures_obs = []

        thread_pool = futures.ThreadPoolExecutor(max_workers=len(self._observers))
        for obs in self._observers:
            futures_obs.append(thread_pool.submit(obs.run_observer))

        return futures_obs


def spawn_document_handlers():
    loop = asyncio.get_event_loop()

    handler1 = Handler(ReportType.REC_CONTRACTS_NO_ITEMS, loop)
    observer_manager1 = ObserverManager(
        handler1,
        r"reports_contracts_no_items")
    observer_manager1.create_observer()

    handler2 = Handler(ReportType.REC_ODNOPOZ_ODNOLOT_LS_NO_CONTRACT_223, loop)
    observer_manager2 = ObserverManager(
        handler2, 
        r"reports_odnopoz_odnolot_ls_no_contract_223")
    observer_manager2.create_observer()

    watcher = Watcher([observer_manager1, observer_manager2])
    return watcher.start_all()
