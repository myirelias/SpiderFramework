# !/usr/bin/env python
# coding=utf-8

import datetime
import json
import time
import threading
from SpiderNode.spider_crawl import SpiderCrawl
from SpiderNode.spider_resolve import SpiderResolve
import redis


class SpiderSchedule(object):
    """
    爬虫调度节点
    必须提供的参数：taskname, headers, xpather_news_list, xpather_href
    非必须参数：mq_host, mq_port, user, psw
    """

    def __init__(self, taskname, headers, xpather_news_list, xpather_href, threadcount=1, **kw):
        self.crawl = SpiderCrawl()
        self.resolve = SpiderResolve()
        self.taskname = taskname
        self.header = headers
        self.xpather_news_list = xpather_news_list
        self.xpather_href = xpather_href
        self.task_queue = '{}:redis_task'.format(taskname)
        self.result_queue = '{}:redis_result'.format(taskname)
        self.sleep_time = kw.get('SLEEP_TIME', 0.5)
        self.redis_host = kw.get('REDIS_HOST')
        self.redis_port = kw.get('REDIS_PORT')
        self.redis_psw = kw.get('REDIS_PSW')
        self.pagecode = kw.get('PAGECODE', 'utf-8')
        self.threadcount = threadcount  # 线程数量
        self.proxy_host = kw.get('PROXY_INFO').get('PROXY_HOST')
        self.proxy_port = kw.get('PROXY_INFO').get('PROXY_PORT')
        self.proxy_user = kw.get('PROXY_INFO').get('PROXY_USER')
        self.proxy_pass = kw.get('PROXY_INFO').get('PROXY_PASS')
        print('spiderschedule init finsh')

    def _schedule_spider(self):
        """
        执行抓取任务
        :return:
        """
        sleep_count = 1
        while True:
            time.sleep(self.sleep_time)  # 防止代理的并发过高
            try:
                current_task = self._schedule_pop_redis(self.task_queue)
                if current_task:
                    sleep_count = 1
                    deal_task = json.loads(current_task)
                    url = deal_task.get('url')
                    task_type = deal_task.get('type')
                    print('{} recive task {}'.format(threading.current_thread().name, url))
                    current_headers = self.header
                    current_headers['Proxy-Switch-Ip'] = 'yes'
                    content = self.crawl.crawl_get_content(url, headers=current_headers,
                                                           proxies=self._schedule_use_proxy(), timeout=5, retry=2,
                                                           pagecode=self.pagecode)
                    res = None
                    if task_type == 'static':
                        res_dict = {}
                        for eachxpath in self.xpather_news_list:
                            res_dict = self.resolve.spider_content_data(content=content, xpather=eachxpath)
                            if res_dict.get('title'):
                                break
                        res_dict['news_url'] = url
                        res_dict['crawl_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        res = {'url': url, 'content': res_dict}
                        # 静态依然要抓urls
                        res_list = self.resolve.spider_content_data(content=content, xpather=self.xpather_href)
                        res_form_static = {'url': url, 'urls': res_list}
                        if res_form_static:
                            savedata = json.dumps(res_form_static)  # 存储到result队列之前需要将dict转为字符串
                            self._schedule_push_redis(self.result_queue, savedata)
                    elif task_type == 'unstatic':
                        res_list = self.resolve.spider_content_data(content=content, xpather=self.xpather_href)
                        res = {'url': url, 'urls': res_list}
                    if res:
                        savedata = json.dumps(res)  # 存储到rabbitmq之前需要将dict转为字符串
                        self._schedule_push_redis(self.result_queue, savedata)
                else:
                    rescount = self._schedule_query_redis(self.result_queue)  # 待处理队列中的数据
                    print('task-[0]\t|\tresult-[{}]\t|\tcurrent times-{}'.format(rescount, sleep_count))
                    time.sleep(sleep_count * 60 * 10)  # 内存溢出的时候休息一会儿 依然获取不到就延长休息时间
                    if rescount <= 0:
                        sleep_count += 1

            except Exception as e:
                print('get task error %s' % e)

    def _schedule_use_proxy(self):
        """
        使用代理ip
        :return: 代理ip
        """
        proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {"host": self.proxy_host,
                                                                     "port": self.proxy_port,
                                                                     "user": self.proxy_user,
                                                                     "pass": self.proxy_pass}
        proxies = {"http": proxy_meta,
                   "https": proxy_meta}

        return proxies


# if __name__ == '__main__':
#     spider = SpiderSchedule()
#     # spider.schedule_start('{}_{}'.format(setting.TASK_NAME, 'task'))
#     p = Pool(setting.SPIDERS)
#     for i in range(8):
#         p.apply_async(spider.schedule_start, args=('{}_{}'.format(setting.TASK_NAME, 'task'),))
#     p.close()
#     p.join()

    def _schedule_push_redis(self, name, data):
        """
        推入数据到redis指定任务列表中
        lpush,将新的数据放在最前面
        :return:
        """
        redis_cli = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_psw, db=0)
        try:
            if isinstance(data, list):
                for each in data:
                    redis_cli.lpush(name, each)
            else:
                redis_cli.lpush(name, data)
        except:
            return

    def _schedule_pop_redis(self, name):
        """
        从指定任务列表中获取数据
        rpop,从最后取
        :return:
        """
        redis_cli = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_psw, db=0)
        try:
            res = redis_cli.rpop(name)
            return res
        except:
            return

    def _schedule_query_redis(self, name):
        """
        查询指定任务列表中数据
        :param name:
        :return:
        """
        redis_cli = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_psw, db=0)
        try:
            res = redis_cli.llen(name)
            return res
        except:
            return

    # 是不是要个多线程

    def schedule_start(self):
        ths = []
        for i in range(self.threadcount):
            th = threading.Thread(target=self._schedule_spider)
            ths.append(th)
            th.start()
        for each_th in ths:
            each_th.join()

#
# if __name__ == '__main__':
#     spider = SpiderSchedule('chinanews', HEADERS, XPATHER_NEWS_LIST, XPATHER_HREF, pagecode='gb2312')
#     spider.schedule_start()