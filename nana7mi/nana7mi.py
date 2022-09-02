import asyncio
import datetime
import os
import sys
from functools import wraps
from importlib import import_module
from typing import Type

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from . import log
from .adapters.basebot import BaseBot
from .adapters.event import Message, MessageType, ParseLimit, limit, on_command


class Nana7mi:
    '基于 OneBot 的机器人框架'
    def __init__(self):
        # 插件集
        self.response = list()
        # 自动任务相关
        self.sched = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.run_time = lambda seconds: datetime.datetime.now() + datetime.timedelta(seconds=seconds)

    def setResponse(self, command = None, plt: ParseLimit = None, priority: float=1.0, block: bool=False):
        def response_function(func):
            @wraps(func)
            @on_command(command)
            @limit(plt)
            async def wrapper(event):
                return await func(event)
            funcInfo = f'(command={command}, priority={priority}, block={block}'
            if plt:
                funcInfo += ''.join([f', {k}={v}' for k, v in plt.items() if v])
            funcInfo += ')'
            for wfunc, info, _ in self.response:
                if wfunc.__name__ == wrapper.__name__ and info == funcInfo:
                    break
            else:
                self.response.append((wrapper, funcInfo, priority))
                self.response.sort(key=lambda p: p[2])
                log.info(f' » {wrapper.__name__}{funcInfo}')
                return wrapper
            return func
        return response_function

    def register_adapter(self, botClass: Type[BaseBot], name: str = '', *args, **kwargs):
        # 安装适配器
        if not name:
            name = botClass.__name__.lower()
        assert issubclass(botClass, BaseBot), f'注册 {name}: {botClass} 时错误，非继承自基础机器人'
        setattr(self, name, botClass(parent=self, name=name, *args, **kwargs))

    def load_builtin_plugins(self):
        log.info('内部模块已导入')
        # 重启命令
        @self.setResponse('/reboot', ParseLimit(white_user=[3099665076, 144115218677563300]))
        async def reboot(event: Message):
            event._receiver._closed = True
            await event._receiver.aws.close_connection()

        # 响应来自 cqbot 的位置命令
        @self.setResponse(command='/here')
        async def here(event: Message):
            if event.message_type == MessageType.Guild:
                return f'该频道ID：{event.guild_id}\n子频道ID：{event.channel_id}'

        # 响应来自 cqbot 的回声命令
        @self.setResponse(command='/echo')
        async def echo(event: Message):
            log.info(str(event), 'echo')
            return event.content.replace('&#91;', '[').replace('&#93;', ']')

        log.info('-------------')
        return self

    def load_plugins(self, folder: str):
        sys.path.append(folder)
        for root, dirs, files in os.walk(folder):
            for file in files:
                if not file.startswith('_') and file.endswith('.py'):
                    try:
                        log.info(f'{file} 已导入')
                        import_module(file.replace('.py', ''))
                        log.info('-------------')
                    except Exception as e:
                        log.error(f'{file} 加载错误：{e}')
            break
        return self

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.sched.start()
        pending = list()
        for name, bot in self.__dict__.items():
            if isinstance(bot, BaseBot):
                log.info(f'{name} 启动中', id='Nana7mi')
                pending.append(bot.run(loop))
        loop.run_until_complete(asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED))
