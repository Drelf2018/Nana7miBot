import asyncio
import logging
from functools import wraps
from json import dumps
from typing import List

from aiowebsocket.converses import AioWebSocket

from . import _group, _private
from .event import Mate, Message, get_event_from_msg


class cqBot():
    logger = logging.getLogger('cqBot')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [cqBot] %(message)s", '%H:%M:%S'))
    logger.addHandler(handler)
    func_params = dict()

    def setResponse(self, command=None, limit={}):
        def response_function(func):
            @wraps(func)
            @Message.on_command(command)
            @Message.limit(**limit)
            async def wrapper(event):
                return await func(event)
            self.response.append(wrapper)
            self.func_params[wrapper] = (command, limit)
            return wrapper
        return response_function

    def __init__(self, url: str = 'ws://127.0.0.1:2434', response: List[callable] = None, debug: bool = False):
        self.url = url
        self.converse = None
        if response:
            self.response = response
        else:
            self.response = []
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    async def connect(self):
        while not self.converse:
            try:
                async with AioWebSocket(self.url) as aws:
                    self.converse = aws.manipulator
            except Exception:
                self.logger.debug('重连中...')
                await asyncio.sleep(3)
        return self.converse.receive

    async def run(self, loop=asyncio.get_event_loop()):
        recv = await self.connect()
        resp = self.response
        while True:
            mes = await recv()
            event = get_event_from_msg(mes)
            if isinstance(event, Mate):
                if event.event_type == 'lifecycle' and event.sub_type == 'connect':
                    self.logger.info('连接成功')
                elif event.event_type == 'heartbeat':
                    self.logger.debug('心跳中，将在 '+str(event.interval/1000)+' 秒后下次心跳 ')
            elif isinstance(event, Message):
                for func in resp:
                    loop.create_task(func(event)).add_done_callback(lambda task: loop.create_task(self.send(task.result())))
                # ok 了家人们 这是最神奇的一行代码 写出它我都感觉自己贼牛
            else:
                self.logger.debug(f'收到信息：{mes.decode("utf-8").strip()}')

    async def send(self, cmd: str | list | tuple | dict):
        if not cmd:
            return
        elif isinstance(cmd, str):
            await self.converse.send(cmd)
        elif isinstance(cmd, (list, tuple)):
            for c in cmd:
                await self.converse.send(c)
        else:
            try:
                js = dumps(cmd, ensure_ascii=False)
                await self.converse.send(js)
            except Exception as e:
                self.logger.error(f'发送失败 {e}')

    async def send_private_msg(self, user_id: int, text: str):
        await self.send(_private % (int(user_id), str(text)))

    async def send_group_msg(self, group_id: int, text: str):
        await self.send(_group % (int(group_id), str(text)))
