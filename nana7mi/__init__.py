import asyncio
import datetime
import logging
import os
import sys
from importlib import import_module

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .adapters.cqBot import cqBot, CQ_PATH
from .adapters.guildBot.guildSTK import guildBot

__the_only_one_bot = None

def get_bot(cqbot: cqBot = None, guildbot: guildBot = None, bilibot=None):
    global __the_only_one_bot
    if not __the_only_one_bot:
        __the_only_one_bot = Nana7mi(cqbot, guildbot, bilibot)
    return __the_only_one_bot

class Nana7mi:
    def info(self, msg: str, id: str = ''):
        self.__logger.info(f'[{id}] {msg}' if id else msg)

    def error(self, msg: str, id: str = ''):
        self.__logger.error(f'[{id}] {msg}' if id else msg)

    def debug(self, msg: str, id: str = ''):
        self.__logger.debug(f'[{id}] {msg}' if id else msg)

    def __init__(self, cqbot: cqBot = None, guildbot: guildBot = None, bilibot=None):
        '基于 OneBot 的机器人框架'
        # 适配器
        self.cqbot = cqbot
        self.guildbot = guildbot
        self.bilibot = bilibot

        # 日志
        self.__logger = logging.getLogger('Nana7mi')
        self.__logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", '%H:%M:%S'))
        self.__logger.addHandler(handler)

        # 自动任务相关
        self.sched = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.run_time = lambda seconds: datetime.datetime.now() + datetime.timedelta(seconds=seconds)

    def load_plugins(self, folder: str):
        sys.path.append(folder)
        for root, dirs, files in os.walk(folder):
            for file in files:
                if not file.startswith('_') and file.endswith('.py'):
                    try:
                        self.info(f'{file} 已导入', id='cqBot')
                        import_module(file.replace('.py', ''))
                        self.info('-------------', id='cqBot')
                    except Exception as e:
                        self.error(f'{file} 加载错误：{e}', id='cqBot')
            break
        return self

    def run(self):
        self.sched.start()
        loop = asyncio.get_event_loop()
        pending = list()
        if self.cqbot:
            self.info('cqBot 启动中', id='Nana7mi')
            pending.append(self.cqbot.run(loop))
        if self.guildbot:
            self.info('guildBot 启动中', id='Nana7mi')
            pending.append(self.guildbot.run(loop))
        loop.run_until_complete(asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED))
