# !/usr/bin/env python
# coding=UTF-8

import time
from framework_crawl import Crawl
from framework_analysis import Spider
from framework_pipeline import Pipe
from framework_setting import XPATHER_HREF


class Engine(object):

    def __init__(self):
        self.crawl = Crawl()
        self.spider = Spider()
        self.pipe = Pipe()

    def _engine_demo(self):
        """
        一个测试demo，爬取的是百度新闻，随便写了个xpath获取了一些链接
        :return:
        """

        url = 'http://news.baidu.com'
        content = self.crawl.crawl_get_content(url, usesession=False, timeout=1)  # 请求页面
        data = self.spider.spider_content_data(content=content, xpather=XPATHER_HREF)  # 解析页面
        saveinfo = []
        for eachdata in data:
            self.pipe.pipe_save_txt(eachdata, 'baidunewslink.txt', savetype='a')  # 存数据到txt文本
            savedict = {'url': eachdata}
            saveinfo.append(savedict)
        txtcontent = self.pipe.pipe_read_txt('baidunewslink.txt')  # 读取txt中的数据
        res = self.pipe.pipe_save_db(saveinfo, 'db_baidunew', 'col_newslink')  # 存储数据到mongodb
        print(res)
        cursor = self.pipe.pipe_read_db('db_baidunew', 'col_newslink')  # 读取mongodb中的数据
        for each in cursor:
            print(each)
        print(txtcontent)

    def excute(self):
        self._engine_demo()


if __name__ == '__main__':
    start = time.time()
    proc = Engine()
    proc.excute()
    end = time.time()
    print('[%.1f s] script finish ' % (end - start))
