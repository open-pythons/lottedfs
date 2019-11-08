# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
sys.path.append("..")
from com.headers import getheaders
from com.ConnectSqlite import ConnectSqlite

if __name__ == "__main__":
    conn = ConnectSqlite('./.SqliteData.db')
    print(conn.fetchall_table('''select sku, original_price, code from originaldata where sku='2069802403';'''))