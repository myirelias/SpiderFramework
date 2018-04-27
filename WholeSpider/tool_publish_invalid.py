# coding=utf-8

from pymongo import MongoClient
import pika
import config as setting
import json

task_name = ['cac_gov', 'cankaoxiaoxi', 'cctv', 'ce_cn', 'china_net', 'cri_net', 'guangming', 'lwdf', 'youth',
             'china_radio', 'chinatoday', 'banyuetan', 'nhfpc', 'mofcom', 'mof_gov', 'ndrc_gov','zgjx', 'wenming', 'k618', 'ccdi_gov']


def query_invalid():
    """
    查询未抓取成功的url
    :return:
    """
    client = MongoClient(
        host=setting.HOST,
        port=27017
    )
    db = client['db_public_invalid']
    col = db['col_{}'.format(setting.TASK_NAME)]
    res = col.find()
    res_list = []
    for each in res:
        res_list.append(each.get('invalid_url'))
    col.delete_many({})
    client.close()
    return res_list


def publish_invalid(pub_data, **kw):
    """发布未抓取成功的url"""
    admin = pika.PlainCredentials(kw.get('user', 'bana'), kw.get('psw', 'root'))
    # 创建rabbitmq链接
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=kw.get('host', setting.HOST),
        port=kw.get('port', 5672),
        virtual_host=kw.get('vhost', '/'),
        credentials=admin
    ))
    # 创建消息通道
    ch = connection.channel()

    for each in pub_data:
        eachdata = {'type': 'static', 'url': each}
        pubdata = json.dumps(eachdata)
        ch.basic_publish(
            exchange=kw.get('exchange', ''),
            routing_key='{}_{}'.format(setting.TASK_NAME, 'task'),
            body=pubdata,
            properties=pika.BasicProperties(
                delivery_mode=2  # 消息持久化
            )
        )
    connection.close()


def deal_invalid(client, colname):
    """
    处理无效数据
    """
    db = client['db_public_opinion']
    col = db[colname]
    res = col.find({'title': ''})
    savedatas = []
    for each in res:
        invalid_url = each.get('url')
        get_time = each.get('get_time')
        savedata = {
            'invalid_url': invalid_url,
            'get_time': get_time
        }
        savedatas.append(savedata)
    col.delete_many({'title': ''})
    client.close()
    print('共计{}条无效数据'.format(len(savedatas)))
    return savedatas


def save_invalid(colname):
    client = MongoClient(
        host=setting.HOST,
        port=27017
    )
    savedata = deal_invalid(client, colname)
    db = client['db_public_invalid']
    col = db[colname]
    for each in savedata:
        col.insert(each)

    client.close()


if __name__ == '__main__':
    invalid_data = query_invalid()
    publish_invalid(invalid_data)
    # for each in task_name:
    #     colname = 'col_' + each
    #     save_invalid(colname)
