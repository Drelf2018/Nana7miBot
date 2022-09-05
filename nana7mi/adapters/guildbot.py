import asyncio
import os
import time
from copy import copy
from json import loads
from typing import Literal, Tuple

import httpx
from bilibili_api import user
from nana7mi import log
from nana7mi.adapters import BaseBot, cqBot
from nana7mi.adapters.event import Message, MessageType, ParseLimit
from plugins._live2pic import Live2Pic
from yaml import Loader, dump, load

SUPER_CHAT = []  # SC的唯一id避免重复记录
ROOM_STATUS = {}  # 直播间开播状态
room_notice ='''指令格式：/stk room []int
在指令后用空格连接多个整数
参数为正整数时添加监控该直播间
参数为负整数时移除直播间的监控
例如指令：

/stk room 21452505 -21470454

表示添加 21452505 监控
同时移除 21470454 监控'''

user_notice = '''指令格式：/stk user []int
在指令后用空格连接多个整数
参数为正整数时添加监控该用户
参数为负整数时移除监控该用户
注意：监控用户仅在子频道生效
例如指令：
/stk user 434334701 -413748120

表示添加 434334701 监控
同时移除 413748120 监控'''

def isInt(m: str) -> Tuple[int, Literal[True]] | Tuple[str, Literal[False]]:
    '判断字符串是否为整数'
    try:
        return int(m), True
    except Exception:
        return m, False

class guildBot(BaseBot):
    def initMap(self):
        # 初始化监听房间、监听用户，以及跳转表
        # 跳转表目的根据已知用户 uid 以及弹幕事件房间 roomid 获取需要推送的频道、子频道号
        self.listening_rooms = set()
        self.listening_users = set()
        self.guildMap = dict()
        if not self.cfg:
            return
        for guild, val in self.cfg.items():
            for roomid in set(val.get('roomid', list())):
                self.listening_rooms.add(roomid)
                for channel, uids in val.items():
                    if channel == 'roomid':
                        continue
                    for uid in set(uids):
                        self.listening_users.add(uid)
                        if gm := self.guildMap.get((uid, roomid)):
                            gm.append((guild, channel))
                        else:
                            self.guildMap[(uid, roomid)] = [(guild, channel)]
        # 快速判断监控用户
        self.users = list(self.listening_users)
        # 将监听房间号告知 biligo-ws-live
        httpx.post(self.BASEURL+'/subscribe', headers={"Authorization": self.aid}, data={'subscribes': list(self.listening_rooms)})

    def __init__(self, parent=None, name: str = '', BASEURL: str = '', aid: str = 'stk', path='./go-cqhttp'):
        '连接 biligo-ws-live 的适配器'
        super().__init__(parent, name, BASEURL + f'/ws?id={aid}', path=path)
        self.BASEURL = BASEURL
        self.aid = aid  #  接入 biligo-ws-live 时的 id 用来区分不同监控程序
        self.url = BASEURL + f'/ws?id={aid}' # biligo-ws-live 运行地址
        self.converse = None  # 异步连接
        # 加载配置文件
        with open(os.path.dirname(__file__)+'\\guildbot.yml', 'r', encoding='utf-8') as fp:
            self.cfg = load(fp, Loader=Loader)
            self.initMap()

    async def run(self, loop=asyncio.get_event_loop()):
        '在执行任务循环前添加插件函数 最后再 super().run(loop)'
        @self.Parent.setResponse('/stk map', ParseLimit(white_user=[144115218677563300]))
        async def queryMap(event: Message):
            if not event.message_type == MessageType.Guild:
                return
            msgs = [f'{k} -> {v}' for k, v in self.guildMap.items() if (int(event.guild_id), int(event.channel_id)) in v]
            return '\n'.join(msgs)

        @self.Parent.setResponse('/stk room')
        async def modifyRoom(event: Message):
            if not event.message_type == MessageType.Guild:
                return
            guild = event.guild_id
            rooms: list = copy(self.cfg.get(int(guild), dict()).get('roomid', list()))

            if not len(event.args):
                return '该频道监控的直播间有：'+str(rooms)[1:-1]
            Add = set()
            Del = set()
            for roomid in event.args:
                roomid, err = isInt(roomid)
                if not err:
                    return f'参数错误：{roomid}\n{room_notice}' if roomid != 'help' else room_notice
                if roomid > 0:
                    if roomid not in rooms:
                        rooms.append(roomid)
                        Add.add(roomid)
                elif roomid < 0:
                    while -roomid in rooms:
                        rooms.remove(-roomid)
                        Del.add(-roomid)
                else:
                    await self.parent.cqbot.send(event.reply('你是不是觉得输入0很有趣？'))
            guildInfo = self.cfg.get(int(guild), dict())
            guildInfo['roomid'] = rooms
            self.cfg[int(guild)] = guildInfo
            self.initMap()
            self.save()
            msg = list()
            if len(Add):
                msg.append(f'新增监控直播间：{str(Add)[1:-1]}')
            if len(Del):
                msg.append(f'移除监控直播间：{str(Del)[1:-1]}')
            return '\n'.join(msg)

        @self.Parent.setResponse('/stk user')
        async def modifyUser(event: Message):
            if not event.message_type == MessageType.Guild:
                return
            guild = event.guild_id
            channel = event.channel_id
            users: list = copy(self.cfg.get(int(guild), dict()).get(int(channel), list()))

            if not len(event.args):
                return '该子频道监控的用户有：'+str(users)[1:-1]

            Add = set()
            Del = set()
            for uid in event.args:
                uid, err = isInt(uid)
                if not err:
                    return f'参数错误：{uid}\n{user_notice}' if uid != 'help' else user_notice
                if uid > 0:
                    if uid not in users:
                        users.append(uid)
                        Add.add(uid)
                elif uid < 0:
                    while -uid in users:
                        users.remove(-uid)
                        Del.add(-uid)
                else:
                    await self.parent.cqbot.send(event.reply('你是不是觉得输入0很有趣？'))
            guildInfo = self.cfg.get(int(guild), dict())
            guildInfo[int(channel)] = users
            self.cfg[int(guild)] = guildInfo
            self.initMap()
            self.save()
            msg = list()
            if len(Add):
                msg.append(f'新增监控用户：{str(Add)[1:-1]}')
            if len(Del):
                msg.append(f'移除监控用户：{str(Del)[1:-1]}')
            return '\n'.join(msg)

        # 获取 cqBot 实例
        self.cb: cqBot = self.Parent.cqbot

        # 连接 biligo-ws-live
        await super().run(loop)

    async def parse(self, mes: bytes):
        js = loads(mes)
        u2 = js['live_info']['name']
        roomid = js['live_info']['room_id']
        match js['command']:
            case 'LIVE':  # 开播
                tt = int(time.time())
                if tt - ROOM_STATUS.get(roomid, 0) > 10800:
                    ROOM_STATUS[roomid] = tt
                    if (uid := js['live_info']['uid']) in self.users:
                        await self.send(uid, roomid, '{name}开播了！\n{title}[CQ:image,file={cover}]'.format_map(js['live_info']))
            
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

            case 'USER_TOAST_MSG':  # 接受到大航海
                data = js['content']['data']
                if (uid := data['uid']) in self.users:
                    u1 = data['username']
                    msg = f'{u1} 在 {u2} 的直播间赠送 {data["role_name"]}￥{data["price"]//1000}'
                    await self.send(uid, roomid, msg)

            case 'SUPER_CHAT_MESSAGE' | 'SUPER_CHAT_MESSAGE_JPN':  # 接受到醒目留言
                data = js['content']['data']
                if int(data['id']) not in SUPER_CHAT and (uid := data['uid']) in self.users:
                    SUPER_CHAT.append(int(data['id']))
                    u1 = data['user_info']['uname']
                    msg = f'{u1} 在 {u2} 的直播间发送' + ' ￥{price} SuperChat 说：{message}'.format_map(data)
                    await self.send(uid, roomid, msg)

            case 'PREPARING':  # 下播
                if (uid := js['live_info']['uid']) in self.users:
                    try:
                        if uid != 434334701:
                            roominfo = await user.User(uid).get_live_info()
                            roomid = roominfo['live_room']['roomid']
                        img = await Live2Pic(uid=uid, roomid=roomid).makePic()
                        tt = int(time.time())
                        img.save(f'{self.PATH}/data/images/live/{uid}_{tt}.png')
                        if uid == 434334701:
                            await self.cb.send_guild_msg(59204391636967121, 9673211, f'[CQ:at,qq=144115218753196143]/post {uid}_{tt}.png')
                        await self.send(uid, roomid, f'[CQ:image,file=live/{uid}_{tt}.png]')
                    except Exception as e:
                        log.error(e, 'pic')
                        await self.send(uid, roomid, f'生成{u2}直播场报失败: {e}')                     

    async def send(self, uid: int, roomid: int, msg: str):
        log.info(f'发送消息: {msg}', 'STKbot')
        for guild_id, channel_id in self.guildMap.get((int(uid), int(roomid)), [(None, None)]):
            if not guild_id or not channel_id:
                break
            else:
                await self.cb.send_guild_msg(guild_id, channel_id, msg)

    def save(self):
        # 加载配置文件
        with open(os.path.dirname(__file__)+'\\guildbot.yml', 'w', encoding='utf-8') as fp:
            dump(self.cfg, fp, allow_unicode=True)
