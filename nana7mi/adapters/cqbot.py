import asyncio
import os
from json import dumps

from yaml import Loader, load

from .basebot import BaseBot
from .event import MessageType, Message

_private = '{\"action\": \"send_private_msg\", \"params\": {\"user_id\": %d, \"message\": \"%s\"}}'
_group = '{\"action\": \"send_group_msg\", \"params\": {\"group_id\": %d, \"message\": \"%s\"}}'
_guild = '{\"action\": \"send_guild_channel_msg\", \"params\": {\"guild_id\": %s, \"channel_id\": %s, \"message\": \"%s\"}}'
obj2js = lambda obj: str(obj).replace('\\', '\\\\').replace('"', '\\"').replace('\\\\n', '\\n')

class cqBot(BaseBot):
    FILEDIR = os.path.dirname(__file__)

    async def send(self, cmd: str | list | tuple | dict):
        if not self.converse:
            self.error('发送消息时错误: cqBot 未连接')
        elif not cmd:
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
                self.error(f'发送消息时错误: {e}')

    async def send_private_msg(self, user_id: int, text: str):
        await self.send(_private % (int(user_id), obj2js(text)))

    async def send_group_msg(self, group_id: int, text: str):
        await self.send(_group % (int(group_id), obj2js(text)))
    
    async def send_guild_msg(self, guild_id: str, channel_id: str, text: str):
        await self.send(_guild % (str(guild_id), str(channel_id), obj2js(text)))

    async def send_all_msg(self, msg: str, id: str = 'default'):
        with open(self.FILEDIR+'\\cqbot.yml', 'r', encoding='utf-8') as fp:
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
            self.error('发送全体消息时错误: %s, %s %s', e, id, msg)

    async def reply(self, event: Message, msg: str):
        '根据消息类型以及输入文字返回可发送至 go-cqhttp 的对应 json 语句'
        if not msg:
            return
        msg = obj2js(msg)
        match event.message_type:
            case MessageType.Private:
                await self.send_private_msg(int(event.user_id), msg)
            case MessageType.Group:
                await self.send_group_msg(int(event.group_id), msg)
            case MessageType.Guild:
                await self.send_guild_msg(event.guild_id, event.channel_id, msg)
