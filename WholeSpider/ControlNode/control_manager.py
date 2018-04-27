# !/usr/bin/env python
# coding=utf-8

import config as setting
from ControlNode.control_task import ControlTask
from ControlNode.control_data import ControlData
import pika
import time
from multiprocessing import Process
import json
import datetime
from imp import reload
import os
import re


class ControlManager(object):
    """
    控制管理器，负责调度任务管理器和数据管理器
    """

    def __init__(self, **kw):
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
            qname = '%s_%s' % (setting.TASK_NAME, each)
            channel.queue_declare(
                queue=qname,
                durable=True
            )
        print('controlmanager init finsh')

    # 使用多进程之后操作消息通道报错，添加该方法，每次连接进行该操作
    @staticmethod
    def _manager_connect_rabbitmq(**kw):
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
        return channel

    def manager_publish_task(self, start_url):
        """
        任务发布
        :param start_url: 起始url
        :return:
        """
        task_manager = ControlTask()
        # 启动时候提供起始url：start_url
        task_manager.task_check(start_url, domain=setting.DOMAIN)
        # 创建消息通道
        ch = self._manager_connect_rabbitmq()
        # 启动后一直循环执行
        while True:
            # 每个小时存储一次已抓取数据 或者每天23点存一次
            if datetime.datetime.now().strftime('%M') == '00' or datetime.datetime.now().strftime('%H') == '23':
                task_manager.task_save(task_manager.old_urls, '../DATA/old_urls.txt')
                task_manager.task_save(task_manager.old_list, '../DATA/old_list.txt')
                # 每个小时重制一次配置文件
                # self._manager_reload_config()
            # 每个小时校验一下是否抓取完全，如果完成则发布起始url循环抓取，并删除列表url以便循环抓取，此处跟据实际需求调整
            elif datetime.datetime.now().strftime('%M') == '30':  # 调试修改
                if self._manager_check_none():
                    task_manager.task_purge('../DATA/old_list.txt')
                    task_manager.old_list = set()
                    time.sleep(120)
            # 控制消息队列数量，防止数据过多
            # task_count = self._manager_msg_count(ch, qname=setting.TASK_NAME + '_task')
            # if task_count >= 10:
            #     # print('wait.....%s new %s' % (task_count, len(task_manager.new_urls)))
            #     time.sleep(5)
            #     continue
            while task_manager.task_has_new():  # 只要存在新增任务则会往对应队列里面推送
                static_task, unstatic_task = task_manager.task_static_unstatic(setting.REGEX_URL)
                all_task = []
                for eachtask in static_task:
                    try:
                        if eachtask.split('.')[-1] in setting.URL_END:
                            continue
                    except:
                        continue
                    current_task = {'type': 'static',
                                    'url': eachtask}
                    all_task.append(json.dumps(current_task))
                for eachtask in unstatic_task:
                    try:
                        if eachtask.split('.')[-1] in setting.URL_END:
                            continue
                    except:
                        continue
                    current_task = {'type': 'unstatic',
                                    'url': eachtask}
                    all_task.append(json.dumps(current_task))
                self._manager_push_msg(all_task, ch, qname=setting.TASK_NAME + '_task')
            n = 5000
            while n:
                n -= 1
                try:
                    url = self._manager_getone_msg(ch, qname=setting.TASK_NAME + '_continue')
                    if url:
                        task_manager.task_check(url.decode('utf-8'), domain=setting.DOMAIN)
                    else:
                        break
                except Exception as e:
                    print(e)

    def _manager_deal_result(self, ch, method, properties, body):
        """
        处理结果队列
        :return:
        """
        # 每个小时重制一次配置文件，此处如果当前分钟内result队列没有任务，则不会重置
        # if datetime.datetime.now().strftime('%M') == '00':
        #     self._manager_reload_config()
        # 取出结果队列中的数据，此处结果队列应返回dict类型的结果
        try:
            result_dict = json.loads(body)
        except Exception as e:
            print(e)
            return
        content = result_dict.get('content')
        urls = result_dict.get('urls')
        if content:
            pushdata = json.dumps(content)
            self._manager_push_msg(pushdata, ch, qname='%s_%s' % (setting.TASK_NAME, 'data'))
        if urls:
            if self._manager_msg_count(ch, qname='{}_{}'.format(setting.TASK_NAME, 'task')) >= setting.MQ_MAXSIZE or \
                            self._manager_msg_count(ch, qname='{}_{}'.format(setting.TASK_NAME,
                                                                             'continue')) >= setting.MQ_MAXSIZE:
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                return
            # -----------BEGIN--------------注意此处--------------BEGIN--------------
            current_url = result_dict.get('url')
            current_urllist = []
            root_url = ''
            # 拼接根url
            if len(current_url.split('/')) > 3:
                root_url = '/'.join(current_url.split('/')[:3])

            for eachurl in urls:
                newurl = ''
                if eachurl:
                    # 无需拼接
                    if eachurl.startswith(('http', 'HTTP')):
                        newurl = eachurl
                    # 默认无效链接
                    elif eachurl.startswith(('#', 'mailto', 'javascript')):
                        continue
                    # 如果以..开头，则要到父级url
                    elif eachurl.startswith('..'):
                        if len(current_url.split('/')) > 4:
                            newurl = '/'.join(current_url.split('/')[0:-2]) + re.sub(re.compile('(\.\.[/]*)+'), '/',
                                                                                     eachurl)
                        elif len(current_url.split('/')) <= 4:
                            if root_url:
                                new_eachurl = re.sub(re.compile('(\.\.[/]*)+'), '/', eachurl)
                                newurl = root_url + new_eachurl
                    # 如果以/开头，则要到根url
                    elif eachurl.startswith('/'):
                        if root_url:
                            newurl = root_url + eachurl
                    # 如果以./开头，则就替换当前位置
                    elif eachurl.startswith('./'):
                        if current_url.endswith('/'):
                            newurl = current_url + eachurl[2::]
                        else:
                            current_url_copy = current_url
                            if len(current_url.split('/')) < 4:
                                continue
                            newurl = current_url_copy.replace(current_url.split('/')[-1], eachurl[2::])
                    # 同./
                    elif eachurl.startswith('.'):
                        if current_url.endswith('/'):
                            newurl = current_url + eachurl[1::]
                        else:
                            current_url_copy = current_url
                            newurl = current_url_copy.replace(current_url.split('/')[-1], eachurl[1::])
                    else:
                        if current_url.endswith('/'):
                            newurl = current_url + eachurl
                        else:
                            current_url_copy = current_url
                            newurl = current_url_copy.replace(current_url.split('/')[-1], eachurl)
                    if newurl:
                        current_urllist.append(newurl)
            # -----------END----------------注意此处--------------END----------------
            self._manager_push_msg(current_urllist, ch, qname='%s_%s' % (setting.TASK_NAME, 'continue'))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def manager_listen_result(self, qname='{}_{}'.format(setting.TASK_NAME, 'result')):
        ch = self._manager_connect_rabbitmq()
        ch.basic_qos(prefetch_count=1)
        ch.basic_consume(self._manager_deal_result,
                         queue=qname)
        ch.start_consuming()

    def manager_save_data(self, **kw):
        """
        存储数据
        配置参数：
        dbname: 数据库名称 colname:集合名称
        :return:
        """
        # 从数据队列中取之并进行存储

        data_manager = ControlData()
        ch = self._manager_connect_rabbitmq()
        while True:
            # 每个小时重制一次配置文件
            # if datetime.datetime.now().strftime('%M') == '00':
            #     self._manager_reload_config()
            # 从数据队列中取之并进行存储
            data = self._manager_getone_msg(ch, qname='%s_%s' % (setting.TASK_NAME, 'data'))
            if data:
                save_data = json.loads(data)
                if save_data.get('title'):
                    data_manager.data_save_db(data=save_data, dbname=kw.get('dbname', 'db_public_opinion'),
                                              colname=kw.get('colname', 'col_' + setting.TASK_NAME))
                else:
                    save_invalid = {'invalid_url': save_data.get('url'),
                                    'get_time': save_data.get('get_time')}
                    data_manager.data_save_db(data=save_invalid, dbname=kw.get('dbname', 'db_public_invalid'),
                                              colname=kw.get('colname', 'col_' + setting.TASK_NAME))
            else:
                time.sleep(10)

    @staticmethod
    def _manager_push_msg(data, ch, **kw):
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
    def _manager_getone_msg(ch, **kw):
        """
        获取消息队列中的信息
        :param kw:
        :return:
        """
        # 创建一个消息通道

        method, header, body = ch.basic_get(
            queue=kw.get('qname', 'default')
        )
        if not method:
            return
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return body

    @staticmethod
    def _manager_msg_count(ch, **kw):
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

    def _manager_check_none(self):
        """
        校验如果非静态队列如果没有url则发布起始url进行循环抓取,并重置存储列表内容
        :return:
        """
        ch = self._manager_connect_rabbitmq()
        have_task = self._manager_getone_msg(ch, qname='%s_%s' % (setting.TASK_NAME, 'task'))
        if not have_task:
            current_task = {'type': 'unstatic',
                            'url': setting.START_URL}
            self._manager_push_msg(json.dumps(current_task), ch, qname='%s_%s' % (setting.TASK_NAME, 'task'))
            return True

        return False

    @staticmethod
    def _manager_reload_config():
        """
        动态加载动态文件,暂时停用
        :return:
        """
        with open(os.path.join(os.path.abspath('..'), 'config.ini'), 'r', encoding='UTF-8') as f:
            with open(os.path.join(os.path.abspath('..'), 'config.py'), 'w', encoding='UTF-8') as fn:
                fn.write(f.read())

        import config as setting
        reload(setting)


if __name__ == '__main__':
    manager = ControlManager()
    # 创建3个进程，分别进行任务发布，结果处理以及数据存储
    proc_task = Process(target=manager.manager_publish_task, args=(setting.START_URL,))  # 此处填写启动url
    proc_result = Process(target=manager.manager_listen_result)
    proc_data = Process(target=manager.manager_save_data)
    proc_task.start()
    proc_result.start()
    proc_data.start()
