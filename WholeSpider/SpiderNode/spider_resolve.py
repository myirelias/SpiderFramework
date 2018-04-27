# !/usr/bin/env python
# coding=UTF-8

from lxml import etree


class SpiderResolve(object):

    def __init__(self):
        pass

    @staticmethod
    def spider_content_data(**kwargs):
        """
        解析content中指定内容，必须传入 content 和 xpather
        :param kwargs: content 为需要解析的页面content, xpather 为xpath解析规则
        :return: 解析后的内容，若xpather为dict类型则返回dict类型，其余返回list
        """

        if 'content' not in kwargs or 'xpather' not in kwargs:
            print('must require enough args')
            return

        xpather = kwargs['xpather']
        content = kwargs['content']

        try:
            selector = etree.HTML(content)
        except:
            selector = content  # 针对需要解析多次的页面采取的方式，前面几次返回的是 etree的element对象，继续解析

        if isinstance(kwargs['xpather'], dict):  # 解析规则以dict的格式传过来的，这种规则默认解析结果为一条数据
            response = {}
            for eachkey in xpather:
                if not xpather[eachkey]:
                    continue
                res = selector.xpath(xpather[eachkey])
                if eachkey == 'publish_time':
                    response[eachkey] = ''.join(res).replace('\n', '').replace('\r', '').replace('\u3000', '')
                else:
                    response[eachkey] = ''.join(res).replace('\n', '').replace('\r', '').replace('\u3000', '').\
                        replace(' ', '')
        elif isinstance(kwargs['xpather'], str):  # 解析规则为str
            response = selector.xpath(kwargs['xpather'])
        else:
            print('xpather must be dict or string')
            return

        return response
