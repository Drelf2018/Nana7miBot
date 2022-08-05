import re
from json import loads
from typing import List

from . import _group, _private, _guild, obj2js


class MessageType:
    Private = 'private'
    Group   = 'group'
    Guild   = 'guild'

class Event:
    def reply(self, msgs: str | list | tuple) -> str | List[str]:
        '根据消息类型以及输入文字返回可发送至 go-cqhttp 的对应 json 语句'
        if isinstance(msgs, str):
            msgs = obj2js(msgs)
            match self.message_type:
                case MessageType.Private:
                    return _private % (int(self.user_id), msgs)
                case MessageType.Group:
                    return _group % (int(self.group_id), msgs)
                case MessageType.Guild:
                    return _guild % (self.guild_id, self.channel_id, msgs)
        elif isinstance(msgs, (list, tuple)):
            match self.message_type:
                case MessageType.Private:
                    return [_private % (int(self.user_id), obj2js(msg)) for msg in msgs]
                case MessageType.Group:
                    return [_group % (int(self.group_id), obj2js(msg)) for msg in msgs]
                case MessageType.Guild:
                    return [_guild % (self.guild_id, self.channel_id, obj2js(msg)) for msg in msgs]

class Mate(Event):
    def __init__(self, js):
        self.time = js.get('time')
        self.event_type = js.get('meta_event_type')
        match self.event_type:
            case 'lifecycle':
                self.sub_type = js.get('sub_type')
            case 'heartbeat':
                self.interval = js.get('interval')

class Message(Event):
    def __init__(self, js: dict):
        # 消息设置
        self.message_type = js.get('message_type')
        # 通用参数
        self.time = js.get('time')
        self.self_id = js.get('self_id')
        self.message_id = js.get('message_id')
        self.message = js.get('message')
        self.raw_message = js.get('raw_message')
        self.user_id = js.get('user_id')
        # 群聊参数
        self.group_id = js.get('group_id')
        # 频道参数
        self.channel_id = js.get('channel_id')
        self.guild_id = js.get('guild_id')
        self.self_tiny_id = js.get('self_tiny_id')
        # 特殊参数
        # self.real_content = ''
        self.text = re.sub(r'\[CQ:(.*?)\]', '', self.message)
        self.at_me = f'[CQ:at,qq={self.self_id}]' in self.message

    def __str__(self):
        return self.message.strip()

    @property
    def content(self) -> str:
        return self.real_content.strip()

    @property
    def args(self) -> list:
        return self.real_content.split()

    def split(self, split_text=' '):
        return self.message.strip().split(split_text)


def get_event_from_msg(msg: bytes) -> Event:
    js = loads(msg)
    match js.get('post_type'):
        case 'message':
            return Message(js)
        case 'meta_event':
            return Mate(js)
