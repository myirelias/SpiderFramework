
# rabbitmq host  # 需要分布式的时候要修改ip
# HOST = '192.168.2.71'
MQ_HOST = 'localhost'
MQ_PORT = 5672

# 爬虫个数
SPIDERS = 4

# 需要过滤的url后缀
URL_END = ['mp3', 'mp4', 'css', 'm4a', 'pdf', 'zip', 'RAR', 'exe', 'rm',
           'avi', 'tmp', 'xls', 'mdf', 'txt', 'doc', 'MID']

# rabbitmq队列限制(大约数量)
MQ_MAXSIZE = 10000

# redis config
# REDIS_HOST = ''
# REDIS_PORT = 6379
# REDIS_DB = 0

REDIS_HOST = '192.168.2.81'
REDIS_PORT = 6379
REDIS_PSW = 'daqsoft@2018'
REDIS_DB = 0

# mongodb
MONGO_HOST = '192.168.2.81'
MONGO_PORT = 27017
MONGO_DB = 'admin'
MONGO_USER = 'spider'
MONGO_PSW = 'daqsoft'
DBNAME_SUCCESS = 'public_news'
DBNAME_FAIL = 'public_news_failed'

# proxy
PROXY_INFO = {
    'PROXY_HOST': '****',
    'PROXY_PORT': '****',
    'PROXY_USER': '****',
    'PROXY_PASS': '****'
}

#
