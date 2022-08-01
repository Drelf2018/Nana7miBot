import asyncio
import datetime
import json
import logging
import os
import sys
import os
import re

import httpx
from importlib import import_module

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .adapter.cqBot import cqBot, Message

CQ_PATH = './go-cqhttp'
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
                self.info(f' » {func.__name__}{self.cqbot.func_params.get(func)}', id='Nana7mi')
            self.info('-------------', id='Nana7mi')
        for root, dirs, files in os.walk(folder):
            for file in files:
                if not file.startswith('_') and file.endswith('.py'):
                    try:
                        import_module(file.replace('.py', ''))
                        self.info(f'{file} 已加载', id='Nana7mi')
                        for func in self.cqbot.response[loaded_plugins:]:
                            self.info(f' » {func.__name__}{self.cqbot.func_params.get(func)}', id='Nana7mi')
                        self.info('-------------', id='Nana7mi')
                        loaded_plugins = len(self.cqbot.response)
                    except Exception as e:
                        self.error(f'{file} 加载错误：{e}', id='Nana7mi')
            break

    def load_buildin_plugins(self):
        if self.cqbot:
            # 响应来自 cqbot 的回声命令
            @self.cqbot.setResponse(command='/echo')
            async def echo(event: Message):
                self.info(str(event), 'echo')
                return event.reply(' '.join(event.args).replace('&#91;', '[').replace('&#93;', ']'))

            # 响应来自 cqbot 的大图命令
            @self.cqbot.setResponse(command='/big')
            async def big(event: Message):
                pics = re.findall(r'[A-Za-z0-9]+\.image', str(event))
                urls = []
                async with httpx.AsyncClient(headers=Headers) as session:
                    for pic in pics:
                        with open(os.path.join(CQ_PATH, 'data', 'images', pic), 'rb') as f:
                            content = f.read()
                            pos = content.find(b'http')
                            url = content[pos:].decode('utf-8')
                            r = await session.get(url)
                            content = r.read()
                            file = pic.replace('.image', '.png')
                            with open(os.path.join(CQ_PATH, 'data', 'images', file), 'wb') as fp:
                                fp.write(content)
                            urls.append(f'[CQ:cardimage,file={file}]')
                return event.reply(urls)

    async def send_all_group_msg(self, text, id=''):
        with open('./nana7mi/config.json', 'r', encoding='utf-8') as fp:
            config = json.load(fp)
        if self.cqbot:
            await self.cqbot.send_private_msg(3099665076, text)
            groups_list = config.get('cqbot', {})
            cqSend = self.cqbot.send_group_msg
            await asyncio.wait([
                asyncio.create_task(cqSend(group_id, text))
                    for group_id in groups_list.get(str(id), groups_list['default'])
            ])

    async def run(self):
        self.info('cqBot 启动中', id='Nana7mi')
        self.sched.start()
        await self.cqbot.run()


__the_only_one_bot = None


def get_bot(cqbot: cqBot = None, khlbot=None, bilibot=None) -> Nana7mi:
    global __the_only_one_bot
    if not __the_only_one_bot:
        __the_only_one_bot = Nana7mi(cqbot, khlbot, bilibot)
    return __the_only_one_bot
