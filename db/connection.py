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
"""
            )
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
"""
            )
        except pyodbc.IntegrityError as err:
            cursor.rollback()
            warnings.warn(str(err))
        else:
            cursor.commit()

    def grant_access(self, nick, report=None, report_category=None):
        assert report is not None or report_category is not None, "Provide report or report category"

        with self.new_cursor() as cursor:
            if report_category is not None:
                cursor.execute(
f"""
DECLARE @user_fk int
DECLARE @reportcategory_fk int

SELECT @user_fk=[User_ID] FROM {self._user_tbl} WHERE Nickname = '{nick}'
SELECT @reportcategory_fk=ReportCategory_ID FROM {self._report_category_tbl} WHERE Name = '{report_category}'

INSERT INTO {self._subscription_tbl} (User_FK, ReportCategory_FK)
VALUES
  (@user_fk, @reportcategory_fk)
"""
                )
            else:
                cursor.execute(
f"""
DECLARE @user_fk int
DECLARE @report_fk int

SELECT @user_fk=[User_ID] FROM {self._user_tbl} WHERE Nickname = '{nick}'
SELECT @report_fk=Report_ID FROM {self._report_tbl} WHERE Name = '{report}'

INSERT INTO {self._subscription_tbl} (User_FK, Report_FK)
VALUES
  (@user_fk, @report_fk)
"""
                )
            cursor.commit()

    def remove_access(self, nick, report=None, report_category=None):
        assert report is not None or report_category is not None, "Provide report or report category"

        with self.new_cursor() as cursor:
            if report_category is not None:
                cursor.execute(
f"""
DECLARE @user_fk int
DECLARE @reportcategory_fk int

SELECT @user_fk=[User_ID] FROM {self._user_tbl} WHERE Nickname = '{nick}'
SELECT @reportcategory_fk=ReportCategory_ID FROM {self._report_category_tbl} WHERE Name = '{report_category}'

DELETE FROM {self._subscription_tbl}
WHERE [User_FK] = @user_fk AND ReportCategory_FK = @reportcategory_fk
"""
                )
            else:
                cursor.execute(
f"""
DECLARE @user_fk int
DECLARE @report_fk int

SELECT @user_fk=[User_ID] FROM {self._user_tbl} WHERE Nickname = '{nick}'
SELECT @report_fk=Report_ID FROM {self._report_tbl} WHERE Name = '{report}'

DELETE FROM {self._subscription_tbl}
WHERE [User_FK] = @user_fk AND Report_FK = @report_fk
"""
                )          
