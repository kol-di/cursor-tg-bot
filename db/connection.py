import pyodbc

from utils.singleton import Singleton


class Server():
    def __init__(self, connection_string):
        self._conn = pyodbc.connect(
            connection_string)
        
    def exec(self, query):
        cursor = self._conn.cursor()
        cursor.execute(query)
        return cursor
    
    def close(self):
        self._conn.close()
