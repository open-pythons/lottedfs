import sqlite3
import asyncio
import aiohttp
import time
import re
from bs4 import BeautifulSoup

start = time.time()
pattern = re.compile('[0-9]+')


async def get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()


async def request():
    url = 'http://chn.lottedfs.cn/kr/search?comSearchWord=2725184485&comCollection=GOODS&comTcatCD=&comMcatCD=&comScatCD=&comPriceMin=&comPriceMax=&comErpPrdGenVal_YN=&comHsaleIcon_YN=&comSaleIcon_YN=&comCpnIcon_YN=&comSvmnIcon_YN=&comGiftIcon_YN=&comMblSpprcIcon_YN=&comSort=RANK%2FDESC&comListCount=20&txtSearchClickCheck=Y'
    result = await get(url)
    soup = BeautifulSoup(result, 'lxml')
    all_span = soup.select('#searchTabPrdList .imgType .listUl .productMd .price span')
    if len(all_span) > 1:
        return ['商品搜索条数错误', 0]
    elif len(all_span) == 1:
        match = pattern.findall(all_span[0].get_text())
        if not match:
            print( ['搜索成功', re.search(r'\d+(\.\d+)?', all_span[0].get_text()).group()])
        else:
            all_strong = soup.select('#searchTabPrdList .imgType .listUl .productMd .discount strong')
            print( ['搜索成功', re.search(r'\d+(\.\d+)?', all_strong[0].get_text()).group()])

tasks = [asyncio.ensure_future(request()) for _ in range(1)]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))

end = time.time()
print('Cost time:', end - start)
