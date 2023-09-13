import pyodbc
import warnings

from utils.singleton import Singleton


class ServerConnection(metaclass=Singleton):
    _user_tbl = '[Cursor].[bot].[User]'
    _report_tbl = '[Cursor].[bot].[Report]'
    _report_category_tbl = '[Cursor].[bot].[ReportCategory]'
    _subscription_tbl = '[Cursor].[bot].[Subscription]'


    def __init__(self, connection_string):
        self._connection_string = connection_string
        self._conn = pyodbc.connect(
            self._connection_string)
        self._conn.autocommit = False

    @staticmethod
    def _reopen_conn(func):
        def wrapper(self, *args, **kwargs):
            try:
                ret = func(self, *args, **kwargs)
            except pyodbc.ProgrammingError:
                print('CONNECTION LOST. RECONNECTING')
                if hasattr(self, '_conn'):
                    self._conn = pyodbc.connect(self._connection_string)
                else:
                    raise Exception("Invalid use of decorator")
                ret = func(self, *args, **kwargs)
            return ret
                
        return wrapper
        
    @_reopen_conn
    def new_cursor(self):
        cursor = self._conn.cursor()
        return cursor
    
    def close(self):
        self._conn.close()

    def all_users(self):
        with self.new_cursor() as cursor:
            cursor.execute(f"SELECT Authorised, Nickname FROM {self._user_tbl}")
            users = cursor.fetchall()
        return users
    
    def get_authorised(self):
        with self.new_cursor() as cursor:
            cursor.execute(f"SELECT Nickname FROM {self._user_tbl} WHERE Authorised = 1")
            users = [usr[0] for usr in cursor.fetchall()]
        return users

    def get_unauthorised(self):
        with self.new_cursor() as cursor:
            cursor.execute(f"SELECT Nickname FROM {self._user_tbl} WHERE Authorised = 0")
            users = [usr[0] for usr in cursor.fetchall()]
        return users

    def add_authorized(self, nick):
        cursor = self.new_cursor()

        try:
            cursor.execute(
f"""
IF EXISTS (SELECT 1 FROM {self._user_tbl} WHERE Nickname = '{nick}')
BEGIN
    UPDATE {self._user_tbl}
    SET Authorised = 1
    WHERE Nickname = '{nick}'
END
ELSE
BEGIN
    INSERT INTO {self._user_tbl} (Authorised, Nickname) 
    VALUES (1, '{nick}')
END
""")
        except pyodbc.IntegrityError as err:
            cursor.rollback()
            warnings.warn(str(err))
        else:
            cursor.commit()

    def add_unauthorized(self, nick):
        cursor = self.new_cursor()

        try:
            cursor.execute(
f"""
IF EXISTS (SELECT 1 FROM {self._user_tbl} WHERE Nickname = '{nick}')
BEGIN
    UPDATE {self._user_tbl}
    SET Authorised = 0
    WHERE Nickname = '{nick}'
END
ELSE
BEGIN
    INSERT INTO {self._user_tbl} (Authorised, Nickname) 
    VALUES (0, '{nick}')
END
""")
        except pyodbc.IntegrityError as err:
            cursor.rollback()
            warnings.warn(str(err))
        else:
            cursor.commit()

    def grant_access(self, nick, report=None, report_category=None):
        if report is None and report_category is None:
            warnings.warn("Either report or report_category should be specified. Resuming")
            return

        with self.new_cursor() as cursor:
            if report_category is not None:
                try:
                    cursor.execute(
f"""
{self.__snippet_user_fk(nick)}
{self.__snippet_reportcategory_fk(report_category)}

INSERT INTO {self._subscription_tbl} (User_FK, ReportCategory_FK)
VALUES
(@user_fk, @reportcategory_fk)
""")
                except pyodbc.IntegrityError:
                    cursor.rollback()
                    warnings.warn(f"Integrity error for user {nick} and report category {report_category}."
                                   "Ensure that both exist")
                else:
                    cursor.commit()

            else:   # if report is not None
                try:
                    cursor.execute(
f"""
{self.__snippet_user_fk(nick)}
{self.__snippet_report_fk(report)}

INSERT INTO {self._subscription_tbl} (User_FK, Report_FK)
VALUES
(@user_fk, @report_fk)
""")
                except pyodbc.IntegrityError:
                    cursor.rollback()
                    warnings.warn(f"Integrity error for user {nick} and report {report}."
                                   "Ensure that both exist")
                else:
                    cursor.commit()


    def remove_access(self, nick, report=None, report_category=None):
        if report is None and report_category is None:
            warnings.warn("Either report or report_category should be specified. Resuming")
            return

        with self.new_cursor() as cursor:
            if report_category is not None:
                cursor.execute(
f"""
{self.__snippet_user_fk(nick)}
{self.__snippet_reportcategory_fk(report_category)}

DELETE FROM {self._subscription_tbl}
WHERE [User_FK] = @user_fk AND ReportCategory_FK = @reportcategory_fk
""")
            else:
                cursor.execute(
f"""
{self.__snippet_user_fk(nick)}
{self.__snippet_report_fk(report)}

DELETE FROM {self._subscription_tbl}
WHERE [User_FK] = @user_fk AND Report_FK = @report_fk
""") 

    def grant_all(self, nick):
        with self.new_cursor() as cursor:
            cursor.execute(
f"""
{self.__snippet_user_fk(nick)}

DELETE FROM {self._subscription_tbl}
WHERE User_FK = @user_fk

INSERT INTO {self._subscription_tbl} (User_FK, ReportCategory_FK)
SELECT 
    @user_fk, 
    ReportCategory_ID 
FROM {self._report_category_tbl}

INSERT INTO {self._subscription_tbl} (User_FK, Report_FK)
SELECT 
    @user_fk, 
    Report_ID 
FROM {self._report_tbl}
""")        

    def remove_all(self, nick):
        with self.new_cursor() as cursor:
            cursor.execute(
f"""
{self.__snippet_user_fk(nick)}

DELETE FROM {self._subscription_tbl}
WHERE User_FK = @user_fk
""")       

    def is_granted(self, nick, report=None, report_category=None):
        if report is None and report_category is None:
            warnings.warn("Either report or report_category should be specified. Resuming")
            return

        with self.new_cursor() as cursor:
            if report_category is not None:
                cursor.execute(
f"""
{self.__snippet_user_fk(nick)}
{self.__snippet_reportcategory_fk(report_category)}

SELECT CASE
    WHEN EXISTS (
        SELECT * FROM {self._subscription_tbl} 
        WHERE User_FK=@user_fk AND ReportCategory_FK=@reportcategory_fk)
    THEN 1
    ELSE 0
END
""")
            else:
                cursor.execute(
f"""
{self.__snippet_user_fk(nick)}
{self.__snippet_report_fk(report)}

SELECT CASE
    WHEN EXISTS (
        SELECT * FROM {self._subscription_tbl} 
        WHERE User_FK=@user_fk AND Report_FK=@report_fk)
    THEN 1
    ELSE 0
END
""")
            return bool(cursor.fetchone()[0])
        

    def all_reports(self, columns=None, no_category=False):
        if columns is None:
            columns = '*'
        else:
            columns = ', '.join(columns)

        with self.new_cursor() as cursor:
            if no_category:
                cursor.execute(f"SELECT {columns} FROM {self._report_tbl} WHERE ReportCategory_FK is NULL")
                reports = cursor.fetchall()
            else:
                cursor.execute(f"SELECT {columns} FROM {self._report_tbl}")
                reports = cursor.fetchall()
        return reports
    
    def all_report_categories(self, columns=None):
        if columns is None:
            columns = '*'
        else:
            columns = ', '.join(columns)

        with self.new_cursor() as cursor:
            cursor.execute(f"SELECT {columns} FROM {self._report_category_tbl}")
            report_categories = cursor.fetchall()
        return report_categories


    def __snippet_user_fk(self, nick):
        return \
f"""
DECLARE @user_fk int
SELECT @user_fk=[User_ID] FROM {self._user_tbl} WHERE Nickname = '{nick}'
"""
    
    def __snippet_report_fk(self, report):
        return \
f"""
DECLARE @report_fk int
SELECT @report_fk=Report_ID FROM {self._report_tbl} WHERE Name = '{report}'
"""
    
    def __snippet_reportcategory_fk(self, report_category):
        return \
f"""
DECLARE @reportcategory_fk int
SELECT @reportcategory_fk=ReportCategory_ID FROM {self._report_category_tbl} WHERE Name = '{report_category}'
"""