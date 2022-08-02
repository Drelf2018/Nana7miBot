import json
import random
import asyncio
import aiohttp
import logging

from aiowebsocket.converses import AioWebSocket

from apscheduler.schedulers.asyncio import AsyncIOScheduler

if __name__ == '__main__':
    from event import get_event_from_data, Pong, Message
else:
    from .event import get_event_from_data, Pong


BASE_URL = 'https://www.kaiheila.cn'
HEADERS = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}
SESSION = None


def watch_data(filename, js):
    filepath = 'D:\\ACGN\\'+filename+'.json'
    with open(filepath, 'w+', encoding='utf-8') as fp:
        json.dump(js, fp, indent=4, ensure_ascii=False)


async def send_command(url: str, params: dict = {'compress': 0}):
    global SESSION
    if not SESSION:
        SESSION = aiohttp.ClientSession(headers=HEADERS)
    resp = await SESSION.get(BASE_URL + url, params=params)
    if resp.status == 200:
        data = await resp.json()
        if data.get('code') == 0:
            return data.get('data')
        else:
            raise Exception(data.get('message'))
    else:
        raise Exception('网络错误')


class khlBot():

    logger = logging.getLogger('khlBot')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[khlBot] [%(asctime)s] [%(levelname)s]: %(message)s", '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(handler)

    def __init__(self, token='1/MTA3Nzk=/GfFI8IADK43TzueQVJ1Gzg==', debug=False):
        self.converse = None
        self.maxSn = 0
        self.session_id = 0

        self.sched = AsyncIOScheduler()
        self.sched.add_job(self.heartbeat, 'interval', seconds=25)

        HEADERS.update({'Authorization': 'Bot '+token})
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    async def guild_list(self):
        data = await send_command('/api/v3/gateway/index')
        return data

    async def get_gateway_url(self):
        data = await send_command('/api/v3/gateway/index')
        return data.get('url')

    async def heartbeat(self):
        await asyncio.sleep(random.randint(0, 10))
        msg = '{"s": 2,"sn": '+str(self.maxSn)+'}'
        self.logger.debug(f'心跳 Ping 事件：{msg}')
        await self.converse.send(msg)

    async def receive(self):
        data = await self.converse.receive()
        return get_event_from_data(data)

    async def connect(self):
        while not self.converse:
            try:
                url = await self.get_gateway_url()
                self.logger.debug(f'获取 Gateway 成功 {url}')
                async with AioWebSocket(url) as aws:
                    self.converse = aws.manipulator
            except Exception as e:
                self.logger.error(f'连接服务端错误 重连中 错误代码 {e}')
                await asyncio.sleep(3)
        hello = await self.receive()
        self.session_id = hello.get_session_id()
        self.logger.info(hello.status())

    async def run(self):
        self.sched.start()
        while True:
            event = await self.receive()
            if isinstance(event, Pong):
                self.logger.debug(f'心跳 Pong 事件：{event}')
            else:
                self.maxSn = max(self.maxSn, event.sn)
                self.logger.info(event)

    async def close(self):
        await SESSION.close()


bot = khlBot(debug=True)
loop = asyncio.get_event_loop()
loop.run_until_complete(bot.connect())
loop.run_until_complete(bot.run())
