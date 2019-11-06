import asyncio
import re
import aiohttp

class Crawler:
    def __init__(self, maxtasks=100):
        self.rooturl = None
        self.loop = None
        self.masterurl = set()
        self.todo = set()
        self.busy = set()
        self.done = {}
        self.tasks = set()
        self.sem = asyncio.Semaphore(maxtasks, loop=self.loop)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.queue = asyncio.Queue(maxsize=100)
        self.count= 1

    @asyncio.coroutine
    def master(self):
        tas = []
        for url in self.rooturl:
            page = [1,20]
            t = asyncio.ensure_future(self.parseMasterurl(url,page),
                                  loop=self.loop)
            tas.append(t)
        yield from asyncio.sleep(1, loop=self.loop)
        while self.busy:
            yield from asyncio.sleep(1, loop=self.loop)
        yield from self.session.close()

        yield from tas
        self.loop.stop()

    @asyncio.coroutine
    def parseMasterurl(self, url,page):
        yield from self.sem.acquire()
        task = asyncio.ensure_future(self.getSuburl(url,page), loop=self.loop)
        task.add_done_callback(lambda t: self.sem.release())
        task.add_done_callback(self.tasks.remove)
        self.tasks.add(task)

    @asyncio.coroutine
    def getSuburl(self, url,page):
        newurl = str(url).format(page[0],page[1])
        self.busy.add(newurl)
        try:
            resp = yield from self.session.get(newurl)
        except Exception as exc:
            print('...', newurl, 'has error', repr(str(exc)))
        else:

            if (resp.status == 200):
                html = (yield from resp.text())
                if html !="[]":

                    json_all_str = re.sub('null|false|true', 'None', html)
                    data_all_list = eval(json_all_str)
                    for item in data_all_list:
                        id = item['id']
                        author_id = item['authorId']
                        suburl = 'http://www.sohu.com/a/{0}_{1}'.format(id, author_id)
                        print("sdd",self.count)
                        self.count=self.count+1
                        yield from self.queue.put(suburl)
                    page[0]= page[0]+1
                    page[1] = page[0]*20
                    asyncio.ensure_future(self.parseMasterurl(url, page),
                                          loop=self.loop)
                else:
                    yield from self.queue.put("")
            resp.close()
            self.done[newurl] = True
        self.busy.remove(newurl)


    @asyncio.coroutine
    def slave(self):
        while True:
            try:
                item = yield from self.queue.get()
                if item != "":
                    yield from self.sem.acquire()
                    task = asyncio.ensure_future(self.process(item), loop=self.loop)
                    task.add_done_callback(lambda t: self.sem.release())
                    task.add_done_callback(self.tasks.remove)
                    self.tasks.add(task)
                if len(self.tasks)==0:
                    item.clear()
                    self.queue.task_done()
                    break
            except:
                pass


    @asyncio.coroutine
    def response(self, item):
        pass

    @asyncio.coroutine
    def process(self, url):
        self.busy.add(url)
        try:
            resp = yield from self.session.get(url)
        except Exception as exc:
            print('...', url, 'has error', repr(str(exc)))
            self.done[url] = False
        else:
            if (resp.status == 200 and
                    ('text/html' in resp.headers.get('content-type'))):
                html = (yield from resp.read())
                data = html.decode('utf-8', 'replace')
                #
                # urls = re.findall(r'(?i)href=["\']?([^\s"\'<>]+)', data)
                # asyncio.Task(self.addurls([(u, url) for u in urls]))
                try:
                    reg = '<meta .*(http-equiv="?Content-Type"?.*)?charset="?([a-zA-Z0-9_-]+)"?'
                    charset = re.findall(reg,data)[0][1]
                except:
                    charset = ""
                if charset != "":
                    charset = charset.lower()
                else:
                    charset = "utf-8"
                text = html.decode(charset, 'replace')
                itme = {}
                itme["url"] = url
                itme["text"] = text
                asyncio.ensure_future(self.response(itme), loop=self.loop)

            resp.close()
            self.done[url] = True
        self.busy.remove(url)
        print(len(self.done), 'completed tasks,', len(self.tasks),
              'still pending, todo', len(self.todo))


class Crawleruning(Crawler):

    def __init__(self):
        super(Crawleruning, self).__init__()
        self.num = 1

    @asyncio.coroutine
    def response(self, item):
        print(self.num)
        self.num=self.num+1


    def main(self,loop):
        self.rooturl = ["http://v2.sohu.com/public-api/feed?scene=CHANNEL&sceneId=10&page={0}&size={1}"]
        self.loop = loop

        tasks = asyncio.gather(  # gather() 可以将一些 future 和协程封装成一个 future
            asyncio.ensure_future(self.master(), loop=loop),
            asyncio.ensure_future(self.slave(), loop=loop)# ensure_future() 可以将一个协程封装成一个 Task
        )
        return tasks

    def start(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main(loop))
        except:
            loop.close()


if __name__ == '__main__':
    import time
    start = time.time()
    crawler = Crawleruning()
    crawler.start()
    end = time.time()
    print("用时",end-start)
