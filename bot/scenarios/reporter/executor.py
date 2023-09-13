from datetime import timedelta
import asyncio
from telethon.errors import MessageTooLongError, PeerIdInvalidError

from db.connection import ServerConnection
from .report_builder import ReportBuilder

conn = ServerConnection()


class ReportExecutor:
    def __init__(self, name, display_name, sp_name, timeout=timedelta(days=1), start=timedelta(hours=9)):
        self._name = name
        self._display_name = display_name
        self._sp_name = sp_name
        self._timeout = timeout
        self._start = start

    async def run_task(self):
        asyncio.sleep(self._start.total_seconds())
        while True:
            try:
                data, columns = conn.execute_sp(self._sp_name)
            except Exception as e:
                raise e
            report = ReportBuilder.from_db(data=data, columns=columns)
            asyncio.create_task(self.__send_reports(report))


    async def __send_reports(self, report):
        for user in self.__subscribed_users():
            asyncio.create_task(self.__send_report(user, report))


    async def __send_report(self, user, report, timeout=10, rowcount_limit=30, colcount_limit=1):
        filename = self._display_name

        try:
            if report.size <= rowcount_limit and len(report.cols) <= colcount_limit:
                try:
                    await asyncio.wait_for(
                        self._bot.send_message(
                            user, 
                            str(report)), 
                            timeout=timeout)
                    
                except MessageTooLongError:
                    await asyncio.wait_for(
                        self._bot.send_file(
                            user, 
                            report.create_file(filename)), 
                            timeout=timeout)
            else:
                await asyncio.wait_for(
                    self._bot.send_file(
                        user, 
                        report.create_file(filename)), 
                        timeout=timeout)
                
        except PeerIdInvalidError:
            print("Unable to send message to user: {}".format(user.nickname))

    async def __subscribed_users(self):
        users = conn.get_users_granted(self._name)
        return [rec[0] for rec in users]