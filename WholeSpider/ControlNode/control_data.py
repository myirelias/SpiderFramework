# !/usr/bin/env python
# coding=UTF-8

import os
try:
    from pymongo import MongoClient
except:
    import pymongo
import config as setting


class ControlData(object):

    def __init__(self):
        self.files = os.path.join(os.path.abspath('DATA'), '%s')
        # self._data_makedir()
        # 此处mongodb是用的台式机ip 根据实际存储位置修改
        self.client = MongoClient(host=setting.HOST, port=27017)

    @staticmethod
    def _data_makedir():  # 当前脚本所在位置若没有DATA文件夹则创建，脚本获取到的数据默认放在该文件夹里
        if not os.path.exists('../DATA'):
            os.makedirs('../DATA')

    def data_save_txt(self, data, filename, savetype='w'):
        """
        储存数据到txt文本,data格式必须为list或str
        :param data: 存储内容
        :param filename: 存储文件名
        :param savetype: 存储类型，默认为 w 重写
        :return: data类型错误返回fail
        """

        with open(self.files % filename, savetype, encoding='UTF-8') as f:
            if isinstance(data, list):
                for eachdata in data:
                    f.write(eachdata + '\n')
            elif isinstance(data, str):
                    f.write(data + '\n')
            else:
                return 'fail'

    def data_read_txt(self, filename, readtype='r'):
        """
        读取txt中的内容并返回
        :param filename: 读取文件名
        :param readtype: 读取方式，默认为 r
        :return: 文件内容的生成器
        """

        return (eachdata for eachdata in open(self.files % filename, readtype, encoding='UTF-8'))

    def data_save_db(self, data, dbname, colname):
        """
        存储内容到mongodb
        :param data: 存储内容，必须为dict或dict组成的list
        :param dbname: 数据库名称
        :param colname: 集合名
        :return: 存储失败则返回 fail
        """

        db = self.client[dbname]
        col = db[colname]
        if isinstance(data, list):
            col.insert_many(data)
        elif isinstance(data, dict):
            col.insert(data)

        return 'save succeed'

    def data_read_db(self, dbname, colname):
        """
        读取mongodb中的数据
        :param dbname: 数据库名称
        :param colname: 集合名称
        :return: mongodb的游标，可遍历
        """
        db = self.client[dbname]
        col = db[colname]
        res = col.find({}, {'_id': 0}, no_cursor_timeout=True)  # 默认返回该集合所有数据，并且游标cursor设置不超时

        return res