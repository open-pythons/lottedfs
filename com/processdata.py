# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import yaml
import atexit
import random
import aiohttp
import asyncio
import sqlite3
import requests
import concurrent
import threading
from bs4 import BeautifulSoup
import sys
import os
import re
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
sys.path.append("..")
from com.ConnectSqlite import ConnectSqlite
from com.headers import getheaders


ip_port = '127.0.0.1:8080'
yamlPath = 'config.yaml'
_yaml = open(yamlPath, 'r', encoding='utf-8')
cont = _yaml.read()
yaml_data = yaml.load(cont, Loader=yaml.FullLoader)
sem = asyncio.Semaphore(10)

conn = ConnectSqlite("./.SqliteData.db")
@atexit.register
def exit_handle():
    conn.close_con()
    print('数据处理结束！')


class Data:

    def __init__(self, timeout=25):
        self.tkList = []
        self.timeout = timeout
        self.pattern = re.compile('[0-9]+')
        self.search_url = 'http://chn.lottedfs.cn/kr/search?comSearchWord={0}&comCollection=GOODS&comTcatCD=&comMcatCD=&comScatCD=&comPriceMin=&comPriceMax=&comErpPrdGenVal_YN=&comHsaleIcon_YN=&comSaleIcon_YN=&comCpnIcon_YN=&comSvmnIcon_YN=&comGiftIcon_YN=&comMblSpprcIcon_YN=&comSort=RANK%2FDESC&comListCount=20&txtSearchClickCheck=Y'
        self.sql = '''select sku, original_price from originaldata ORDER BY random() LIMIT 10;'''

    def getIpPort(self):
        ip_port = conn.fetchall_table('SELECT * FROM proxyip ORDER BY random() LIMIT 1;')
        if isinstance(ip_port, list) and len(ip_port) == 1:
            return ip_port[0][0]
        else:
            raise RuntimeError('Ip代理数量不足，程序被迫停止，请运行获取代理Ip.exe')

    def get_urls(self, sku_list):
        sku_urls = [[self.search_url.format(item[0]), item[1]] for item in sku_list]
        return sku_urls

    def processhtml(self, html, sku_url):
        soup = BeautifulSoup(html, 'lxml')
        all_span = soup.select('#searchTabPrdList .imgType .listUl .productMd .price span')
        if len(all_span) > 1:
            print('商品搜索条数错误', 0)
        elif len(all_span) == 1:
            match = self.pattern.findall(all_span[0].get_text())
            if match:
                price = re.search(r'\d+(\.\d+)?', all_span[0].get_text()).group()
            else:
                all_strong = soup.select('#searchTabPrdList .imgType .listUl .productMd .discount strong')
                price = re.search(r'\d+(\.\d+)?', all_strong[0].get_text()).group()
        else:
            print('商品没有搜到', 0, sku_url[0])

    async def get(self, url):
        global ip_port
        headers = getheaders()
        async with sem:
            async with aiohttp.ClientSession(headers=headers) as session:
                try:
                    async with session.get(url, timeout=self.timeout, proxy='http://' + ip_port) as resp:
                        if resp.status == 200:
                            return await resp.read()
                        else:
                            return False
                except (aiohttp.client_exceptions.ClientProxyConnectionError,aiohttp.ClientHttpProxyError,aiohttp.ClientProxyConnectionError) as cpce:
                    print('代理Ip：{0} 已失效'.format(ip_port))
                    conn.delete_table('''DELETE FROM proxyip WHERE ip_port='{0}';'''.format(ip_port))
                    ip_port = '140.143.196.172:8001'
                    return False
                except (aiohttp.client_exceptions.ClientOSError, aiohttp.client_exceptions.ServerDisconnectedError, aiohttp.client_exceptions.ClientConnectorError) as cce:
                    print('客户端断网失败')
                    return False
                except (concurrent.futures._base.TimeoutError, aiohttp.client_exceptions.ServerTimeoutError) as ste:
                    print('数据请求超时')
                    return False
                except Exception as e:
                    print('其他异常错误',type(e))
                    return False

    async def request(self, sku_url):
        if len(sku_url) < 2:
            return
        html = await self.get(sku_url[0])
        if html:
            tk = threading.Thread(target=self.processhtml, args=(html, sku_url,))
            tk.start()
            self.tkList.append(tk)
        else:
            print('数据请求失败，等待下次重新请求')
            return

    def get_data(self):
        global ip_port
        ip_port = '140.143.196.172:8001'
        while True:
            sku_list = conn.fetchall_table(self.sql)
            if len(sku_list) <= 0:
                break
            sku_urls = self.get_urls(sku_list)
            tasks = [asyncio.ensure_future(self.request(sku_url)) for sku_url in sku_urls]
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait(tasks))
            break
        for tk in self.tkList:
            tk.join()

if __name__ == "__main__":
    start = time.time()
    sql = '''CREATE TABLE `processdata` (
            `sku` VARCHAR(12) DEFAULT NULL PRIMARY KEY,
            `original_price` VARCHAR(9) DEFAULT NULL,
            `new_price` VARCHAR(9) DEFAULT NULL,
            `code` int(1) DEFAULT NULL
            )'''
    print('创建处理数据表成功' if conn.create_tabel(sql) else '创建处理数据表失败')
    d = Data()
    d.get_data()
    print("运行完毕，总用时:{}".format(time.time() - start))
