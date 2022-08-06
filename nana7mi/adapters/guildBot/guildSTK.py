import asyncio
import os
from json import dumps, loads

import httpx
from aiowebsocket.converses import AioWebSocket
from yaml import Loader, load

BASEURL = 'http://localhost:8080'
SUPER_CHAT = []  # SC的唯一id避免重复记录


class guildBot:
    # 加载配置文件
    with open(os.path.dirname(__file__)+'\\config.yml', 'r', encoding='utf-8') as fp:
        cfg = load(fp, Loader=Loader)

    # 初始化监听房间、监听用户，以及跳转表
    # 跳转表目的根据已知用户 uid 以及弹幕事件房间 roomid 获取需要推送的频道、子频道号
    listening_rooms = set()
    listening_users = set()
    guildMap = dict()
    for guild, val in cfg.items():
        for roomid in val['roomid']:
            listening_rooms.add(roomid)
            for channel, uids in val.items():
                if channel == 'roomid':
                    continue
                for uid in uids:
                    listening_users.add(uid)
                    if gm := guildMap.get((uid, roomid)):
                        gm.append((guild, channel))
                    else:
                        guildMap[(uid, roomid)] = [(guild, channel)]

    def __init__(self, aid: str, url: str = BASEURL+'/ws'):
        '连接 biligo-ws-live 的适配器'
        self.aid = aid  #  接入 biligo-ws-live 时的 id 用来区分不同监控程序
        self.url = url + f'?id={aid}' # biligo-ws-live 运行地址
        self.converse = None  # 异步连接

    async def connect(self):
        '异步建立 ws 连接'
        while not self.converse:  # 多次尝试连接 biligo-ws-live
            try:
                async with AioWebSocket(self.url) as aws:
                    self.converse = aws.manipulator
            except Exception:
                self.parent.info('biligo-ws-live 重连中', 'STK')
                await asyncio.sleep(3)
        self.parent.info('biligo-ws-live 连接成功', 'STK')
        return self.converse.receive  # 接受消息的函数

    async def run(self, loop=asyncio.get_event_loop()):
        from nana7mi import get_bot
        self.parent = get_bot()

        # 连接 biligo-ws-live
        recv = await self.connect()

        # 将监听房间号告知 biligo-ws-live
        httpx.post(BASEURL+'/subscribe', headers={"Authorization": self.aid}, data={'subscribes': list(self.listening_rooms)})

        # 快速判断监控用户
        self.users = list(self.listening_users)

        while True:  # 死循环接受消息
            try:
                loop.create_task(self.parse(await recv()))
            except Exception as e:
                self.parent.error(f'接收消息时错误: {e}', 'STK')
                break

    async def parse(self, mes: bytes):
        js = loads(mes)
        u2 = js['live_info']['name']
        roomid = js['live_info']['room_id']
        match js['command']:
            case 'INTERACT_WORD':  # 进入直播间
                if (uid := int(js['content']['data']['uid'])) in self.users:
                    u1 = js['content']['data']['uname']
                    await self.send(uid, roomid, f'{u1} 进入了 {u2} 的直播间')

            case 'DANMU_MSG':  # 接受到弹幕
                info = js['content']['info']
                if (uid := int(info[2][0])) in self.users:
                    u1 = info[2][1]
                    await self.send(uid, roomid, f'{u1} 在 {u2} 的直播间说：{info[1]}')

            case 'SEND_GIFT':  # 接受到礼物
                data = js['content']['data']
                if (uid := data['uid']) in self.users:
                    u1 = data['uname']
                    msg = f'{u1} 在 {u2} 的直播间' + '{action} {giftName}'.format_map(data) + f'￥{data["price"]/1000}'
                    await self.send(uid, roomid, msg)

            case 'GUARD_BUY':  # 接受到大航海
                data = js['content']['data']
                if (uid := data['uid']) in self.users:
                    u1 = data['username']
                    msg = f'{u1} 在 {u2} 的直播间赠送 {data["gift_name"]}￥{data["price"]//1000}'
                    await self.send(uid, roomid, msg)

            case 'SUPER_CHAT_MESSAGE' | 'SUPER_CHAT_MESSAGE_JPN':  # 接受到醒目留言
                data = js['content']['data']
                if int(data['id']) not in SUPER_CHAT and (uid := data['uid']) in self.users:
                    SUPER_CHAT.append(int(data['id']))
                    u1 = data['user_info']['uname']
                    msg = f'{u1} 在 {u2} 的直播间发送' + ' ￥{price} SuperChat 说：{message}'.format_map(data)
                    await self.send(uid, roomid, msg)

    async def send(self, uid: int, roomid: int, msg: str):
        self.parent.info(f'发送消息: {msg}', 'STK')
        for guild_id, channel_id in self.guildMap.get((int(uid), int(roomid)), [(None, None)]):
            if not guild_id or not channel_id:
                break
            else:
                await self.parent.cqbot.send_guild_msg(guild_id, channel_id, msg)
