import json
from user import User


class Event:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return str(self.data)


class Hello(Event):
    def __init__(self, data):
        super().__init__(data)
        self.code = data['d']['code']

    def get_session_id(self):
        return self.data['d']['session_id']

    def status(self):
        status_code = {
            0: '连接成功',
            40100: '缺少参数',
            40101: '无效的 token',
            40102: 'token 验证失败',
            40103: 'token 过期'
        }
        return status_code[self.code]


class Pong(Event):
    pass


class Message(Event):
    '''
    channel_type	string	消息频道类型, GROUP 为频道消息
    type	        int     1:文字消息, 2:图片消息，3:视频消息，4:文件消息， 8:音频消息，9:KMarkdown，10:card 消息，255:系统消息, 其它的暂未开放
    target_id	    string	发送目的 id，如果为是 GROUP 消息，则 target_id 代表频道 id
    author_id	    string	发送者 id, 1 代表系统
    content	        string	消息内容, 文件，图片，视频时，content 为 url
    msg_id	        string	消息的 id
    msg_timestamp	int     消息发送时间的毫秒时间戳
    nonce	        string	随机串，与用户消息发送 api 中传的 nonce 保持一致
    extra	        mixed	不同的消息类型，结构不一致
    '''
    def __init__(self, data):
        super().__init__(data)
        self.sn = data.get('sn')
        d = data.get('d')
        self.isGroup = d.get('channel_type') == 'GROUP'
        self.type = d.get('type')
        self.target_id = d.get('target_id')
        self.author_id = d.get('author_id')
        self.content = d.get('content')
        self.msg_id = d.get('msg_id')
        self.msg_timestamp = d.get('msg_timestamp')
        self.nonce = d.get('nonce')
        self.extra = d.get('extra')
        if not self.type == 255 and self.isGroup:
            self.guild_id = self.extra.get('guild_id')
            self.channel_name = self.extra.get('channel_name')
            self.mention = self.extra.get('mention')
            self.mention_all = self.extra.get('mention_all')
            self.mention_roles = self.extra.get('mention_roles')
            self.mention_here = self.extra.get('mention_here')
        self.author = User(self.extra.get('author'))

    def __str__(self):
        info = '收到来自 ' + self.author.get_full_info() + ' 的消息：'
        info += self.content
        return info


SUBEVENT = {
    0: Message,
    1: Hello,
    3: Pong
}


def get_event_from_data(data):
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        if isinstance(data, str):
            data = json.loads(data)
        return SUBEVENT.get(data['s'], Event)(data)
    except Exception as e:
        print(data, f'运行时错误 {e} line: {e.__traceback__.tb_lineno}')
