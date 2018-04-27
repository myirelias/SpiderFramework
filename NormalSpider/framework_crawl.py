# !/usr/bin/env python
# coding=UTF-8

import requests


class Crawl(object):
    def __init__(self):
        self.session = requests.Session()

    def crawl_get_content(self, url, usesession=True, **kw):
        """
        get请求页面，并返回content,请使用params,proxies,timeout,pagecode, headers命名参数
        :param url: 请求地址
        :param usesession: 使用session标识，默认True
        :param kw: 关键字参数
        :return: 页面的content
        """

        retry = 5  # 重试次数
        response = 'no_data'
        while retry:
            retry -= 1
            try:
                if usesession:  # 使用session请求
                    res = self.session.get(url, params=kw.get('params', ''), headers=kw.get('headers', ''),
                                           proxies=kw.get('proxies', ''), timeout=kw.get('timeout', 30))
                else:  # 不使用session请求
                    res = requests.get(url, params=kw.get('params', ''), headers=kw.get('headers', ''),
                                       proxies=kw.get('proxies', ''), timeout=kw.get('timeout', 30))
                if res.status_code == 200:  # 状态码为200则立刻终止，否则重试
                    response = res.content.decode(kw.get('pagecode', 'UTF-8'))
                    break
                else:
                    continue
            except Exception as e:
                print('[requests page error] %s' % e)
                continue

        return response

    def crawl_post_content(self, url, usesession=True, **kw):
        """
        post请求页面，并返回content，请使用data,proxies,timeout,pagecode, headers命名参数
        :param url: 请求地址
        :param usesession: 使用session请求，默认为True
        :param kw: 关键字参数
        :return: 返回页面content
        """

        retry = 5
        response = 'no_data'
        while retry:
            retry -= 1
            try:
                if usesession:
                    res = self.session.post(url, data=kw.get('params', ''), headers=kw.get('headers', ''),
                                           proxies=kw.get('proxies', ''), timeout=kw.get('timeout', 30))
                else:
                    res = requests.post(url, data=kw.get('params', ''), headers=kw.get('headers', ''),
                                       proxies=kw.get('proxies', ''), timeout=kw.get('timeout', 30))
                if res.status_code == 200:
                    response = res.content.decode(kw.get('pagecode', 'UTF-8'))
                    break
                else:
                    continue
            except Exception as e:
                print('[requests page error] %s' % e)
                continue

        return response
