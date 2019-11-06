# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3

class ConnectSqlite:

    def __init__(self, dbName="./.Proxies.db"):
        self._conn = sqlite3.connect(
            dbName, timeout=3, isolation_level=None, check_same_thread=False)
        self._conn.execute('PRAGMA synchronous = OFF')
        self._cur = self._conn.cursor()
        self._time_now = "[" + \
            sqlite3.datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + "]"

    def close_con(self):
        self._cur.close()
        self._conn.close()

    def create_tabel(self, sql):
        try:
            self._cur.execute(sql)
            self._conn.commit()
            return True
        except Exception as e:
            print(self._time_now, "[CREATE TABLE ERROR]", e)
            return False

    def delete_table(self, sql):
        try:
            if 'DELETE' in sql.upper():
                self._cur.execute(sql)
                self._conn.commit()
                return True
            else:
                print(self._time_now, "[EXECUTE SQL IS NOT DELETE]")
                return False
        except Exception as e:
            print(self._time_now, "[DELETE TABLE ERROR]", e)
            return False

    def fetchall_table(self, sql, limit_flag=True):
        try:
            self._cur.execute(sql)
            war_msg = self._time_now + \
                ' The [{}] is empty or equal None!'.format(sql)
            if limit_flag is True:
                r = self._cur.fetchall()
                return r if len(r) > 0 else war_msg
            elif limit_flag is False:
                r = self._cur.fetchone()
                return r if len(r) > 0 else war_msg
        except Exception as e:
            print(self._time_now, "[SELECT TABLE ERROR]", e)

    def insert_update_table(self, sql):
        try:
            self._cur.execute(sql)
            self._conn.commit()
            return True
        except Exception as e:
            print(self._time_now, "[INSERT/UPDATE TABLE ERROR]", e, " [", sql, "]")
            return False
    
    def insert_table_many(self, sql, value):
        try:
            self._cur.executemany(sql, value)
            self._conn.commit()
            return True
        except Exception as e:
            print(self._time_now, "[INSERT MANY TABLE ERROR]", e)
            return False
