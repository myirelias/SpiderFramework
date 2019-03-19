# !/usr/bin/env python
# coding=utf-8

import os
import pickle
from hashlib import md5
import re
import redis


class ControlTask(object):
    """
    任务管理器，负责任务相关操作，如校验是否新增，读取已抓取任务文本
    """
    def __init__(self, taskname, redis_host, redis_port, redis_psw):
        # self._mkdata()
        # 实例化两个bloomfilter
        self.bloom_urls = BloomFilter(host=redis_host, port=redis_port, psw=redis_psw,
                                      blockNum=6, key='bloomfilter_pub')  # url的过滤器，分6个块存,内存空间默认512M
        # list的过滤器，默认1个块存,内存空间给32M
        self.bloom_list = BloomFilter(host=redis_host, port=redis_port, psw=redis_psw,
                                      key='{}:redis_list'.format(taskname), bit_size=1 << 28)
        self.new_urls = set()
        self.redis_cli = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_psw)

    @staticmethod
    def _task_read(path):
        """
        任务加载方法
        :param path: 存储位置
        :return: 加载内容
        """
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
                return data
        except Exception as e:
            print('[error] %s not exists, create it now' % path)
            open(path, 'w')

        return set()

    @staticmethod
    def task_save(data, path):
        """
        存储数据
        :param data: 存储内容
        :param path: 存储位置
        :return:
        """
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    @staticmethod
    def _mkdata():
        """
        创建data文件夹，用于存放数据
        :return:
        """
        if not os.path.exists('../DATA'):
            os.makedirs('../DATA')

    def task_check(self, task, **kw):
        """
        任务检验，是否为新增任务
        :param task: task内容，此处为url
        :return:
        """
        if isinstance(task, str):
            task_list = [task]
        elif isinstance(task, list):
            task_list = task
        else:
            print('task must be list or str, not %s' % type(task))
            return

        # 这里页面匹配规则可能因网站需要修改
        # 此处应该单独封装起来
        for eachtask in task_list:
            # 控制抓取的域
            domains = kw.get('domain', [])
            for eachdomain in domains:  # 多个domain循环
                if eachdomain not in eachtask:  # 若个任务连接不在domain内，则切换下一个domain
                    continue
                else:  # 若任务连接在domain内，则break跳出循环，for...else中的内容不会执行，则此任务链接会被进行后续处理
                    break
            else:
                continue
            if not self.bloom_urls.isContains(eachtask) and not self.bloom_list.isContains(eachtask):
                self.new_urls.add(eachtask)

    def task_has_new(self):
        """
        是否有新增任务
        :return: 如果有新增任务，则返回具体任务数量，否则返回false
        """
        if self.new_urls:
            return len(self.new_urls)
        else:
            return False

    def task_static_unstatic(self, regexer):
        """
        区分新增静态任务和非静态任务
        :return:依次返回静态任务和非静态任务
        """
        static_task = []
        unstatic_task = []
        while self.new_urls:
            url = self.new_urls.pop()
            if self.task_regex(url, regexer):
                static_task.append(url)
                self.bloom_urls.insert(url)
            else:
                unstatic_task.append(url)
                self.bloom_list.insert(url)

        return static_task, unstatic_task

    @staticmethod
    def task_regex(data, regexer):
        """
        正则过滤url,按照静态新闻页面和非静态新闻页面划分
        :param data: 需要过滤的url
        :return: 静态 True 非静态 False
        """
        pattern = re.compile(regexer, re.S)
        res = re.search(pattern, data)
        if res:
            return True

        return False

    @staticmethod
    def task_purge(path):
        """
        清理数据
        :param path:
        :return:
        """
        with open(path, 'wb') as f:
            pickle.dump(set(), f)

    def task_redis_del(self, key=None):
        """
        删除redis对应的键
        目前用在循环抓取时候，清空列表url，
        列表url每次循环只抓取一遍，直至下次循环
        :return:
        """
        if not key:
            return
        res = self.redis_cli.delete(key)
        return res

    def task_push_redis(self, name, data):
        """
        推入数据到redis指定任务列表中
        lpush,将新的数据放在最前面
        :return:
        """

        try:
            if isinstance(data, list):
                for each in data:
                    self.redis_cli.lpush(name, each)
            else:
                self.redis_cli.lpush(name, data)
        except:
            return

    def task_pop_redis(self, name):
        """
        从指定任务列表中获取数据
        rpop,从最后取
        :return:
        """
        try:
            res = self.redis_cli.rpop(name)
            return res
        except:
            return

    def task_query_redis(self, name):
        """
        查询指定任务列表中数据
        :param name:
        :return:
        """
        try:
            res = self.redis_cli.llen(name)
            return res
        except:
            return


class SimpleHash(object):
    """
    简单的hash算法
    """
    def __init__(self, cap, seed):
        self.cap = cap

        self.seed = seed

    def hash(self, value):
        ret = 0

        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])

        return (self.cap - 1) & ret


class BloomFilter(object):

    def __init__(self, host='localhost', port=6379, db=0, psw='', blockNum=1,
                 key='bloomfilter_pub', bit_size=1 << 32):

        """

        :param host: the host of Redis

        :param port: the port of Redis

        :param db: witch db in Redis

        :param blockNum: one blockNum for about 90,000,000; if you have more strings for filtering, increase it.

        :param key: the key's name in Redis

        """

        self.server = redis.Redis(host=host, port=port, db=db, password=psw)

        self.bit_size = bit_size  # Redis的String类型最大容量为512M

        # self.seeds = [5, 7, 11, 13, 31, 37, 61]
        self.seeds = [5, 11, 31]

        self.key = key

        self.blockNum = blockNum

        self.hashfunc = []

        for seed in self.seeds:
            self.hashfunc.append(SimpleHash(self.bit_size, seed))

    def isContains(self, str_input):

        if not str_input:
            return False

        m5 = md5()

        m5.update(str_input.encode('utf-8'))

        str_input = m5.hexdigest()

        ret = True

        name = self.key + str(int(str_input[0:2], 16) % self.blockNum)

        for f in self.hashfunc:
            loc = f.hash(str_input)

            ret = ret & self.server.getbit(name, loc)

        return ret

    def insert(self, str_input):

        m5 = md5()

        m5.update(str_input.encode('utf-8'))

        str_input = m5.hexdigest()

        name = self.key + str(int(str_input[0:2], 16) % self.blockNum)

        for f in self.hashfunc:
            loc = f.hash(str_input)

            self.server.setbit(name, loc, 1)


