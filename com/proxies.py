# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import threading
import requests
import sqlite3
import asyncio
import aiohttp
import random
import atexit
import yaml
import time
import sys
import os


sem = asyncio.Semaphore(50) # 信号量，控制协程数，防止爬的过快
yamlPath = 'config.yaml'
_yaml = open(yamlPath, 'r', encoding='utf-8')
cont = _yaml.read()
yaml_data = yaml.load(cont, Loader=yaml.FullLoader)
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
sys.path.append("..")
from com.ConnectSqlite import ConnectSqlite
from com.headers import getheaders


conn = ConnectSqlite("./.SqliteData.db")
@atexit.register
def exit_handle():
    conn.close_con()
    print('代理Ip提取结束')


class Proxies:

    def __init__(self, count=2, url='http://www.xicidaili.com', step=9, timeout=10):
        self.count = count
        self.url = url
        self.step = step
        self.urls = []
        self.tkList = []
        self.timeout = timeout
        self.targeturl = 'http://icanhazip.com/'

    def get_urls(self):
        self.urls = ['{0}/nn/{1}'.format(self.url, r)
                     for r in range(1, self.count)]
        self.urls.extend(['{0}/nt/{1}'.format(self.url, r)
                          for r in range(1, self.count)])
        self.urls.extend(['{0}/wt/{1}'.format(self.url, r)
                          for r in range(1, self.count)])

    def slice(self):
        self.urls = [self.urls[i:i+self.step]
                     for i in range(0, len(self.urls), self.step)]

    def checkip(self, ip):
        headers = getheaders()
        proxies = {"http": "http://" + ip, "https": "http://" + ip}  # 代理ip
        requests.adapters.DEFAULT_RETRIES = 3
        proxyIP = "".join(ip.split(":")[0:1])
        try:
            response = requests.get(
                url=self.targeturl, proxies=proxies, headers=headers, timeout=10, verify=False)
            if proxyIP in response.text:
                return True
            else:
                return False
        except Exception:
            print('代理Ip: {0} 已失效'.format(ip))
            return False

    def findip(self, html):
        soup = BeautifulSoup(html, 'lxml')
        all = soup.find_all('tr', class_='odd')
        for i in all:
            t = i.find_all('td')
            ip = t[1].text + ':' + t[2].text
            is_avail = self.checkip(ip)
            if is_avail:
                sql = """INSERT INTO proxyip VALUES ('{0}');""".format(ip)
                print('代理Ip: {0} 插入成功'.format(ip) if conn.insert_update_table(
                    sql) else '代理Ip: {0} 插入失败'.format(ip))

    async def get(self, u):
        headers = getheaders()
        async with sem:
            async with aiohttp.ClientSession(headers=headers) as session:
                try:
                    async with session.get(u, timeout=self.timeout) as resp:
                        return await resp.text()
                except Exception:
                    print('异常数据跳过')

    async def request(self, u):
        result = await self.get(u)
        tk = threading.Thread(target=self.findip, args=(result,))
        tk.start()
        self.tkList.append(tk)

    def process(self):
        for url in self.urls:
            tasks = [asyncio.ensure_future(self.request(u)) for u in url]
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait(tasks))
        for tk in self.tkList:
            tk.join()


if __name__ == "__main__":
    count = yaml_data.get('COUNT')
    count = count if count else 2
    sql = '''CREATE TABLE `proxyip` (
                      `ip_port` VARCHAR(25) DEFAULT NULL PRIMARY KEY
                    )'''
    print('创建代理表成功' if conn.create_tabel(sql) else '创建代理表失败')
    p = Proxies(count=count, step=5)
    p.get_urls()
    p.slice()
    p.process()
