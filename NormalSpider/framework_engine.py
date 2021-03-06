# !/usr/bin/env python
# coding=UTF-8

import time
from configparser import ConfigParser

from framework_crawl import Crawl
from framework_analysis import Analysis
from framework_pipeline import Pipeline

setting_file = './framework_setting.conf'


class Engine:

    def __init__(self):
        self.crawl = Crawl()
        self.pipe = Pipeline()
        self.analysis = Analysis()
        self.conf = self._engine_load_config()

    def _engine_demo(self):
        """
        一个测试demo
        :return:
        """

        print('test sucess!')

    @staticmethod
    def _engine_load_config():
        """
        加载配置文件
        :return:
        """
        conf = ConfigParser()
        conf.read(setting_file, encoding='utf-8')
        return conf

    def excute(self):
        self._engine_demo()


if __name__ == '__main__':
    start = time.time()
    proc = Engine()
    proc.excute()
    end = time.time()
    print('{:.1f}s script finish '.format(end - start))
