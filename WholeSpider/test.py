# coding=utf-8
import pika
import config as setting
import json
import time
from pymongo import MongoClient


def publish_invalid(ch, method, properties, body):
    """
    查询未抓取成功的url
    :return:
    """
    each = json.loads(body)
    url = each.get('static')
    save_data = {'invalid_url': url}
    col.insert(save_data)
    ch.basic_ack(delivery_tag=method.delivery_tag)


client = MongoClient(
        host=setting.HOST,
        port=27017
    )
db = client['db_public_invalid']
col = db['col_{}'.format('chinatoday')]
# 创建登录验证信息
admin = pika.PlainCredentials('bana', 'root')
# 创建rabbitmq链接
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=setting.HOST,
    port=5672,
    virtual_host='/',
    credentials=admin
))
# 创建消息通道
channel = connection.channel()
# 声明消息队列
channel.basic_consume(
    publish_invalid,
    queue='chinatoday_task'
)
channel.start_consuming()
''.upper()
