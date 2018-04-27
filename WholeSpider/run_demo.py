"""
启动任务
"""

from ControlNode.control_manager import ControlManager
from SpiderNode.spider_schedule import SpiderSchedule
from multiprocessing import Process, Pool
import config as setting


if __name__ == '__main__':

    manager = ControlManager()
    # 创建3个进程，分别进行任务发布，结果处理以及数据存储
    proc_task = Process(target=manager.manager_publish_task, args=(setting.START_URL,))  # 此处填写启动url
    proc_result = Process(target=manager.manager_listen_result)
    proc_data = Process(target=manager.manager_save_data)
    proc_task.start()
    proc_result.start()
    proc_data.start()
    spider = SpiderSchedule()
    p = Pool(setting.SPIDERS)
    for i in range(setting.SPIDERS):
        p.apply_async(spider.schedule_start, args=('{}_{}'.format(setting.TASK_NAME, 'task'),))
    p.close()
    p.join()