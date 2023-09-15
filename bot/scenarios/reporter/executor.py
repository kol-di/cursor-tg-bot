from datetime import timedelta
import asyncio
from telethon.errors import MessageTooLongError, PeerIdInvalidError

from .report_builder import ReportBuilder


class ReportExecutor:
    def __init__(self, bot, conn, name, display_name, sp_name, timeout=timedelta(days=1), start=timedelta(hours=9)):
        self._bot = bot
        self._conn = conn

        self._name = name
        self._display_name = display_name
        self._sp_name = sp_name
        self._timeout = self.abs_time_to_timedelta(timeout)
        self._start = self.abs_time_to_timedelta(start)
        print(f'created executor {self._display_name}')

    async def run_task(self):
        await asyncio.sleep(self._start.total_seconds())
        while True:
            try:
                data, columns = self._conn.execute_sp(self._sp_name)
            except Exception as e:
                raise e
            
            report = ReportBuilder.from_db(data=data, columns=columns)
            await asyncio.create_task(self.__send_reports(report))
            await asyncio.sleep(self._timeout.total_seconds())


    async def __send_reports(self, report):
        print(f'sending report {self._display_name}')
        for user in self.__subscribed_users():
            await asyncio.create_task(self.__send_report(user, report))


    async def __send_report(self, user, report, timeout=60, rowcount_limit=30, colcount_limit=1):
        filename = self._display_name

        try:
            if report.size <= rowcount_limit and len(report.cols) <= colcount_limit:
                try:
                    await asyncio.wait_for(
                        self._bot.send_message(
                            user, 
                            filename + '\n' + str(report)), 
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

    def __subscribed_users(self):
        users = self._conn.get_users_granted(self._name)
        return [rec[0] for rec in users]
    

    @classmethod
    def create_executors(cls, bot, conn):
        reports = conn.get_reports()
        executors = []
        for rep in reports:
            inst = cls(bot, conn, *rep)
            executors.append(inst)
        return executors
    
    @staticmethod
    def abs_time_to_timedelta(time):
        return timedelta(
            hours=time.hour, 
            minutes=time.minute, 
            seconds=time.second, 
            microseconds=time.microsecond
        )