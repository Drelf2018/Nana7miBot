import asyncio
import datetime
import json
import logging
import os
import sys
from importlib import import_module

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .adapter.cqBot import cqBot

CQ_PATH = 'C:/Users/drelf/Desktop/nanamiBot'
Headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}

class Nana7mi:
    _logger = logging.getLogger('Nana7mi')
    _logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", '%H:%M:%S'))
    _logger.addHandler(handler)

    def info(self, msg: str, id: str = ''):
        self._logger.info(f'[{id}] {msg}' if id else msg)

    def error(self, msg: str, id: str = ''):
        self._logger.error(f'[{id}] {msg}' if id else msg)

    def debug(self, msg: str, id: str = ''):
        self._logger.debug(f'[{id}] {msg}' if id else msg)

    def __init__(self, cqbot: cqBot = None, khlbot=None, bilibot=None):
        self.cqbot = cqbot
        self.khlbot = khlbot
        self.bilibot = bilibot
        self.sched = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.run_time = lambda seconds: datetime.datetime.now() + datetime.timedelta(seconds=seconds)

    def load_plugins(self, folder: str):
        sys.path.append(folder)
        loaded_plugins = len(self.cqbot.response)
        if loaded_plugins:
            self.info('已加载内部模块', id='Nana7mi')
            for func in self.cqbot.response:
                self.info(f' » {func.__name__}()', id='Nana7mi')
        for root, dirs, files in os.walk(folder):
            for file in files:
                if not file.startswith('_') and file.endswith('.py'):
                    try:
                        import_module(file.replace('.py', ''))
                        self.info(f'{file} 已加载', id='Nana7mi')
                        for func in self.cqbot.response[loaded_plugins:]:
                            self.info(f' » {func.__name__}()', id='Nana7mi')
                        loaded_plugins = len(self.cqbot.response)
                    except Exception as e:
                        self.error(f'{file} 加载错误：{e}', id='Nana7mi')
            break

    async def send_all_group_msg(self, text, id=''):
        with open('./nana7mi/config.json', 'r', encoding='utf-8') as fp:
            config = json.load(fp)
        if self.cqbot:
            await self.cqbot.send_private_msg(3099665076, text)
            groups_list = config.get('cqbot', {})
            cqSend = self.cqbot.send_group_msg
            await asyncio.wait([
                asyncio.create_task(cqSend(group_id, text))
                    for group_id in groups_list.get(id, groups_list['default'])
            ])

    async def run(self):
        self.info('cqBot 启动中', id='Nana7mi')
        self.sched.start()
        await self.cqbot.run()


__the_only_one_bot = None


def get_bot(cqbot=None, khlbot=None, bilibot=None):
    global __the_only_one_bot
    if not __the_only_one_bot:
        __the_only_one_bot = Nana7mi(cqbot, khlbot, bilibot)
    return __the_only_one_bot
