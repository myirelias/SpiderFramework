# !/usr/bin/env python
# coding=utf-8

from SpiderNode.spider_crawl import SpiderCrawl
from SpiderNode.spider_resolve import SpiderResolve
import config as setting
import pika
import time
import json
from multiprocessing import Pool
import datetime
import os


class SpiderSchedule(object):
    """
    爬虫调度节点
    """

    def __init__(self, **kw):
        self.crawl = SpiderCrawl()
        self.resolve = SpiderResolve()
        # 创建rabbitmq消息队列，队列命名通过配置文件中TASK_NAME来确定
        # 参数设置：user: 用户名 psw: 密码 host: 主机ip port: 端口号 vhost: 虚拟主机
        # 消息队列：
        # task_unstatic: 任务队列，控制节点用于发布需要抓取的非静态(非新闻，如列表页面)任务
        # task_static: 任务队列，控制节点用于发布需要抓取的静态(新闻内容页面)任务
        # result: 结果队列，主要用于爬虫节点反馈爬取结果的队列
        # continue:新增队列，用于数据处理器获取其中反馈的新任务交给任务管理器
        # data: 数据存储队列，用于数据处理器获取其中需要存储的数据进行储存
        self.queue_name = ['task', 'result', 'continue', 'data']
        # 创建登录验证信息
        admin = pika.PlainCredentials(kw.get('user', 'bana'), kw.get('psw', 'root'))
        # 创建rabbitmq链接
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=kw.get('host', setting.HOST),
            port=kw.get('port', 5672),
            virtual_host=kw.get('vhost', '/'),
            credentials=admin
        ))
        # 创建消息通道
        channel = connection.channel()
        # 声明消息队列
        for each in self.queue_name:
            qname = '{}_{}'.format(setting.TASK_NAME, each)
            channel.queue_declare(
                queue=qname,
                durable=True
            )
        print('spiderschedule init finsh')

    @staticmethod
    def schedule_connect_rabbitmq(**kw):
        """
        创建rabbitmq服务，打开消息通道
        :param kw: 参数配置
        :return: 消息通道
        """
        admin = pika.PlainCredentials(kw.get('user', 'bana'), kw.get('psw', 'root'))
        connect = pika.BlockingConnection(pika.ConnectionParameters(
            host=kw.get('host', setting.HOST),
            port=kw.get('port', 5672),
            virtual_host=kw.get('vhost', '/'),
            credentials=admin
        ))
        channel = connect.channel()

        return channel

    def _schedule_spider(self, ch, method, properties, body):
        """
        执行抓取任务
        :return:
        """

        time.sleep(1)  # 防止代理的并发过高
        try:
            # current_task = self._schedule_pullone_msg(ch, qname='{}_{}'.format(setting.TASK_NAME, 'task'))
            current_task = body
            if current_task:
                deal_task = json.loads(current_task)
                url = deal_task.get('url')
                task_type = deal_task.get('type')
                print('recive task {}'.format(url))
                current_headers = setting.HEADERS
                current_headers['Proxy-Switch-Ip'] = 'yes'
                content = self.crawl.crawl_get_content(url, headers=current_headers,
                                                       proxies=self._schedule_use_proxy(), timeout=5, retry=2)
                res = None
                if task_type == 'static':
                    res_dict = {}
                    for eachxpath in setting.XPATHER_NEWS_LIST:
                        res_dict = self.resolve.spider_content_data(content=content, xpather=eachxpath)
                        if res_dict.get('title'):
                            break
                    res_dict['url'] = url
                    res_dict['get_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    res = {'url': url, 'content': res_dict}
                elif task_type == 'unstatic':
                    res_list = self.resolve.spider_content_data(content=content, xpather=setting.XPATHER_HREF)
                    res = {'url': url, 'urls': res_list}
                if res:
                    savedata = json.dumps(res)  # 存储到rabbitmq之前需要将dict转为字符串
                    self._schedule_push_msg(savedata, ch, qname='%s_%s' % (setting.TASK_NAME, 'result'))
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                print('no task')
                time.sleep(2)
        except Exception as e:
            print('get task error %s' % e)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    @staticmethod
    def _schedule_pullone_msg(ch, **kw):
        """
        获取消息队列中的信息
        :param kw:
        :return:
        """
        # 创建一个消息通道

        method, header, body = ch.basic_get(
            queue=kw.get('qname', 'default'),
            no_ack=True
        )
        if not method:
            return
        else:
            # ch.basic_ack(delivery_tag=method.delivery_tag)
            return body

    @staticmethod
    def _schedule_push_msg(data, ch, **kw):
        """
        推送消息到消息队列
        配置参数：
        exchange:交换机 qname:消息队列名称
        :param data: 待推送的内容
        :param kw: 配置参数
        :return:
        """
        if isinstance(data, str):
            pushdata = [data]
        elif isinstance(data, list):
            pushdata = data
        else:
            print('data must be list or str')
            return

        for eachdata in pushdata:
            ch.basic_publish(
                exchange=kw.get('exchange', ''),
                routing_key=kw.get('qname', 'default'),
                body=eachdata,
                properties=pika.BasicProperties(
                    delivery_mode=2  # 消息持久化
                )
            )

    @staticmethod
    def _schedule_msg_count(ch, **kw):
        """
        获取消息队列中的信息
        :param kw:
        :return: messsage count
        """
        # 创建一个消息通道

        method, header, body = ch.basic_get(
            queue=kw.get('qname', 'default')
        )

        if not method:
            return 0
        else:
            ch.basic_reject(delivery_tag=method.delivery_tag)
            try:
                return int(method.message_count)
            except:
                return 0

    def schedule_start(self, qname='{}_{}'.format(setting.TASK_NAME, 'task')):
        ch = self.schedule_connect_rabbitmq()
        ch.basic_qos(prefetch_count=1)
        ch.basic_consume(
            self._schedule_spider,
            queue=qname
        )
        ch.start_consuming()

    @staticmethod
    def _schedule_use_proxy():
        """
        使用代理ip
        :return: 代理ip
        """
        proxy_host = "****"
        proxy_port = "****"
        proxy_user = "****"
        proxy_pass = "****"
        proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {"host": proxy_host,
                                                                     "port": proxy_port,
                                                                     "user": proxy_user,
                                                                     "pass": proxy_pass}
        proxies = {"http": proxy_meta,
                   "https": proxy_meta}

        return proxies


if __name__ == '__main__':
    spider = SpiderSchedule()
    # spider.schedule_start('{}_{}'.format(setting.TASK_NAME, 'task'))
    p = Pool(setting.SPIDERS)
    for i in range(8):
        p.apply_async(spider.schedule_start, args=('{}_{}'.format(setting.TASK_NAME, 'task'),))
    p.close()
    p.join()