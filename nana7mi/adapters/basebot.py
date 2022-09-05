import asyncio

from aiowebsocket.converses import AioWebSocket, Converse

from nana7mi import log
from .event import Mate, Message, get_event_from_msg

class BaseBot:
    _closed: bool = False
    converse: Converse = None

    def info(self, msg: str):
        log.info(msg, self.name)

    def error(self, msg: str):
        log.error(msg, self.name)

    def debug(self, msg: str):
        log.debug(msg, self.name)

    def __init__(self, parent, name: str, url: str = '', path: str = ''):
        self.url = url
        self.name = name
        self.__path = path
        from nana7mi import Nana7mi
        self._parent: Nana7mi = parent

    @property
    def PATH(self) -> str:
        return self.__path

    @property
    def Parent(self):
        return self._parent

    async def connect(self):
        while not self.converse:
            try:
                async with AioWebSocket(self.url) as aws:
                    self.aws = aws
                    self.converse = aws.manipulator
            except Exception:
                self.debug('重连中...')
                await asyncio.sleep(3)
        self.info('连接成功')
        return self.converse.receive

    async def run(self, loop=asyncio.get_event_loop()):
        recv = await self.connect()
        while not self._closed:  # 死循环接受消息
            try:
                loop.create_task(self.parse(await recv()))
            except Exception as e:
                self.error(f'接收消息时错误: {e}')
                break
        self.info('连接已断开')

    async def reply(self, event, msg: str):
        ...

    async def parse(self, mes: bytes):
        event = get_event_from_msg(mes, self)
        if isinstance(event, Mate):
            match event.event_type:
                case 'lifecycle':
                    if event.sub_type != 'connect':
                        self.error('连接失败')
                case 'heartbeat':
                    self.debug('心跳中，将在 '+str(event.interval/1000)+' 秒后下次心跳 ')
        elif isinstance(event, Message):
            for func, funcInfo, _ in self.Parent.response:
                await self.reply(event, await func(event))
                if 'block=True' in funcInfo:
                    break
        else:
            self.debug(f'收到信息：{mes.decode("utf-8").strip()}')
