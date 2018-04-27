# 每日中国
TASK_NAME = 'chinatoday'

# 起始URL
START_URL = 'http://www.chinatoday.com.cn/'

# 控制域，必须为list格式
DOMAIN = ['chinatoday.com.cn']
# 请求头
HEADERS = {
    'Host': 'www.chinatoday.com.cn',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:52.0) Gecko/20100101 Firefox/52.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Cookie': 'wdcid=051b1b5beee1610d; wdlast=1523245358',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# xpath规则
XPATHER_HREF = ".//*/@href"
# 字段模版
# {
#     "title": "",
#     "publish_time": "",
#     "source": "",
#     "author": "",
#     "belong": "",
#     "content": "",
#     "editor": "",
# },
XPATHER_NEWS_LIST = [
    {
        "title": ".//*[@class='CT_DetailsTitle']/text()",
        "publish_time": ".//*[@class='CT_DetailsTime']/text()",
        "soruce": "substring-after(.//*[contains(text(),'来源')],'来源：')",
        "author": "substring-after(.//*[contains(text(),'作者')],'作者：')",
        "belong": ".//*[@class='CurrChnlCls']/descendant::text()",
        "content": ".//*[@class='TRS_Editor']/descendant::p/text()",
        "editor": "",
    }
]

# 文件位置
FN_OLD_URLS = 'old_urls.txt'

# 正则匹配规则,此处为静态页面url的正则表达式，匹配以下的规则的网址将抓取其中新闻内容
REGEX_URL = r'/\d{4,6}/\w*\d{4,6}_\d+\.[s]*htm[l]*'

# rabbitmq host
HOST = '192.168.2.54'

# 爬虫个数
SPIDERS = 8

# 需要过滤的url后缀
URL_END = ['mp3', 'mp4', 'css', 'm4a', 'pdf']

# rabbitmq队列限制(大约数量)
MQ_MAXSIZE = 10000