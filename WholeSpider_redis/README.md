# 2019.03.19
- 对url拼接方案进行了优化

# 2018.10.29 爬虫框架 v5.0

迭代内容

- 取消使用rabbitmq作为消息队列，使用redis作任务发布以及结果反馈

基于redis的5.0版本抓取框架说明
- 控制节点
	- 任务发布
		- 首次发布任务时需要校验是否所有url已完成抓取(去redis-task查)
		- 若首次则发布初始Url，若非首次则取待继续抓取的url进行发布
	- 结果处理
		- redis-result中取出结果数据进行处理
		- 待抓取的url发布到redis-task中，待存储的数据进行存储
- 爬虫节点
	- 对任务进行爬取
- redis中间件
	- bloomfilter过滤器存redis
	- redis消息队列
		1. 控制节点发布任务到redis-task
		2. 爬虫节点从redis-task中取出任务进行爬取
		3. 爬虫节点将爬取结果存储到redis-result中
		4. 控制节点从redis-result中取出结果进行处理得到：
			1> 待继续抓取的url
			2> 待存储的数据
			3> 无效url
		5. 控制节点将待存储数据存储到指定位置
		6. 控制节点将无效的url抛弃
		7. 控制节点将待继续抓取的任务发布到redis-task中
		8. 至步骤2进行循环

## 2018.10.17 爬虫框架 V4.0

迭代内容

- 静态页面抓取新闻后依然要抓取该页面的所有urls
- 新增Config包
- 启动方式修改为参数启动，启动时提供启动任务对应的config文件名(‘_’后的内容)
- 通用配置写在Config下面的configuration.py中
- 启动入口均为run_engine，所有文件配置完config_<taskname>.py文件后即可直接启动抓取任务

## 2018.10.17 爬虫框架 V3.0


迭代内容

- 修改去重方法，使用redis+bloomfilter进行以抓取数据的去重
- 每次抓取的list型url存在指定redis位置，每次循环的时候删除
- ControlTask模块中urls，list使用bloom过滤器处理 存在redis中
- 启动时校验task队列和continue、result队列

## 2018.03.19 爬虫框架 V2.0

针对全站爬取开发的新的爬虫框架，使用rabbitmq作为通信工具

- 控制节点
	- 控制管理模块：
		1. 初始化方法，初始化时候创建五个rabbitmq队列，用于任务的发布 
		2. 任务发布方法，第一次执行时发布起始url到task队列中，之后从新增任务队列中获取新的任务发布到task队列 
		3. 结果处理方法，将爬虫节点返回的结果进行提取，将url发布到新增任务队列，将数据发布到数据队列 
		4. 数据处理方法，从数据队列取出数据进行存储，目前存储在mongodb中
	- 任务管理模块：
		1. 新增任务校验，区分新增url和已抓取url
		2. 区分静态新闻url和非静态新闻url
		3. 对url进行md5处理
		4. 对已抓取的链接进行持久化操作
	- 数据处理模块：对数据进行存储或读取指定位置数据
	- 启动模块：三个进程同时启动三个模块
- 爬取节点
	- 爬虫调度模块[原]：
		- 静态新闻页面爬虫，每次从队列中取出一条url进行爬取，结果返回至result队列中
		- 非静态新闻页面爬虫，每次从相应队列中取出一条url进行爬取，结果返回至result队列中
    - 爬虫调度模块[v2.0]
        - 任务执行爬虫，从队列中取出任务，使用任务中type字段区分待处理内容，作出相应的处理
	- 页面下载模块：进行URL请求，获取页面html
	- 页面解析模块：对页面html按照一定解析规则进行解析
	- 启动模块