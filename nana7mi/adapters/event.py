import re
from functools import wraps
from json import loads
from typing import List, TypedDict

class MessageType:
    Private = 'private'
    Group   = 'group'
    Guild   = 'guild'

class Event:
    def setReceiver(self, recv):
        self._receiver = recv
        return self
    
    async def reply(self, msg: str):
        return await self._receiver.reply(self, msg)

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
        self.real_content = ''
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

class ParseLimit(TypedDict):
    '''包含用户、群聊、频道的黑白名单 如果存在白名单会忽略黑名单
    params: at_me 表示是否@机器人
    params: callback 判断不通过时的回复，现仅支持在字符中插入 {user_id} 表示发送人QQ号(频道号)'''
    white_user: List[int]
    banned_user: List[int]
    white_group: List[int]
    banned_group: List[int]
    white_channel: List[int]
    banned_channel: List[int]
    at_me: bool
    callback: str

def get_event_from_msg(msg: bytes, recv):
    js = loads(msg)
    match js.get('post_type'):
        case 'message':
            return Message(js).setReceiver(recv)
        case 'meta_event':
            return Mate(js).setReceiver(recv)

async def failed_return(msg: str = ''):
    return msg

def limit(plt: ParseLimit):
    def check_event(white: list, banned: list, eid: int) -> bool:
        if white:
            if (int(eid) in white) or (str(eid) in white):
                return True
        elif banned:
            if (int(eid) not in banned) and (str(eid) not in banned):
                return True
        else:
            return True
        return False

    check_user = lambda user_id: check_event(plt.get('white_user'), plt.get('banned_user'), user_id)
    check_group = lambda group_id: check_event(plt.get('white_group'), plt.get('banned_group'), group_id)
    check_channel = lambda channel_id: check_event(plt.get('white_channel'), plt.get('banned_channel'), channel_id)

    def check(func):
        if not plt:
            return func
        @wraps(func)
        def wrapped_function(event: Message):
            msg = plt.get('callback', '').format(user_id=event.user_id)
            if not check_user(event.user_id):
                return failed_return(msg)
            match event.message_type:
                case MessageType.Private:
                    return func(event)
                case MessageType.Group:
                    if plt.get('at_me') and not event.at_me:
                        return failed_return(msg)
                    return func(event) if check_group(event.group_id) else failed_return(msg)
                case MessageType.Guild:
                    if plt.get('at_me') and not event.at_me:
                        return failed_return(msg)
                    return func(event) if check_channel(event.channel_id) else failed_return(msg)
        return wrapped_function
    return check

def on_command(command=None):
    def check(func):
        @wraps(func)
        def wrapped_function(event: Message):
            if command and not str(event).startswith(command):
                return failed_return()
            event.real_content = str(event).replace(command, '') if command else str(event)
            return func(event)
        return wrapped_function
    return check
