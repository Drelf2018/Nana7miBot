import asyncio
import logging
import os
import re
from copy import copy
from functools import wraps
from json import dumps
from typing import List

import httpx
from aiowebsocket.converses import AioWebSocket
from yaml import Loader, load

from . import _group, _guild, _private, limit, obj2js, on_command
from .event import Mate, Message, get_event_from_msg

Headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}
CQ_PATH = './go-cqhttp'
FILEDIR = os.path.dirname(__file__)

class cqBot():
    logger = logging.getLogger('cqBot')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [cqBot] %(message)s", '%H:%M:%S'))
    logger.addHandler(handler)
    func_params = dict()

    def setResponse(self,
        command = None,
        white_user = list(),
        banned_user = list(),
        white_group = list(),
        banned_group = list(),
        white_channel = list(),
        banned_channel = list(),
        at_me = False,
        group_both_user = False,
        channel_both_user = False,
        callback: str = ''
    ):
        def response_function(func):
            @wraps(func)
            @on_command(command)
            @limit(
                white_user, banned_user,
                white_group, banned_group,
                white_channel, banned_channel,
                at_me, group_both_user, channel_both_user,
                callback
            )
            async def wrapper(event):
                return await func(event)
            self.response.append(wrapper)
            self.func_params[wrapper] = '(' + ', '.join([f'{k}={v}' for k, v in locals().items() if k not in ['wrapper', 'func', 'self'] and v]) + ')'
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

    def load_buildin_plugins(self):
        # 响应来自 cqbot 的回声命令
        @self.setResponse(command='/echo')
        async def echo(event: Message):
            # self.info(str(event), 'echo')
            await self.send_all_msg(event, 'echo')
            return event.reply(event.content.replace('&#91;', '[').replace('&#93;', ']'))

        # 响应来自 cqbot 的大图命令
        @self.setResponse(command='/big')
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
        return self

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
                match event.event_type:
                    case 'lifecycle':
                        if event.sub_type == 'connect':
                            self.logger.info('连接成功')
                        else:
                            self.logger.error('连接失败')
                    case 'heartbeat':
                        self.logger.debug('心跳中，将在 '+str(event.interval/1000)+' 秒后下次心跳 ')
            elif isinstance(event, Message):
                for func in resp:
                    loop.create_task(func(copy(event))).add_done_callback(lambda task: loop.create_task(self.send(task.result())))
                # ok 了家人们 这是最神奇的一行代码 写出它我都感觉自己贼牛
            else:
                self.logger.debug(f'收到信息：{mes.decode("utf-8").strip()}')

    async def send(self, cmd: str | list | tuple | dict):
        if not cmd:
            return
        elif isinstance(cmd, str):
            print(cmd)
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
        await self.send(_private % (int(user_id), obj2js(text)))

    async def send_group_msg(self, group_id: int, text: str):
        await self.send(_group % (int(group_id), obj2js(text)))
    
    async def send_guild_msg(self, guild_id: str, channel_id: str, text: str):
        await self.send(_guild % (str(guild_id), str(channel_id), obj2js(text)))

    async def send_all_msg(self, msg: str, id: str = 'default'):
        with open(FILEDIR+'\\config.yml', 'r', encoding='utf-8') as fp:
            config = load(fp, Loader=Loader)
        pending = set()
        for cid in ['admin', str(id)]:
            for user in config.get(cid, {}).get('users', []):
                pending.add(self.send_private_msg(user, msg))
            for group in config.get(cid, {}).get('group', []):
                pending.add(self.send_group_msg(group, msg))
            for guild in config.get(cid, {}).get('guild', []):
                pending.add(self.send_guild_msg(guild['guild_id'], guild['channel_id'], msg))
        try:
            await asyncio.wait(pending)
        except Exception as e:
            self.logger.error('发送全体消息时错误: %s, %s %s', e, id, msg)
