import re
from functools import wraps
from json import loads

from . import _group, _private

    
class Event():
    def __init__(self):
        self.isResponse = False
        self.isAccept = False

    def accept(self):
        self.isAccept = True

    def ignore(self):
        self.isAccept = False

    def reply(self, text):
        if isinstance(text, str):
            if self.isGroup:
                return _group % (int(self.group_id), str(text))
            else:
                return _private % (int(self.user_id), str(text))
        elif isinstance(text, (list, tuple)):
            if self.isGroup:
                return [_group % (int(self.group_id), str(t)) for t in text]
            else:
                return [_private % (int(self.user_id), str(t)) for t in text]


class Mate(Event):
    def __init__(self, js):
        super().__init__()
        self.event_type = js.get('meta_event_type')
        self.self_id = js.get('self_id')
        self.time = js.get('time')
        if self.event_type == 'lifecycle':
            self.sub_type = js.get('sub_type')
        elif self.event_type == 'heartbeat':
            self.interval = js.get('interval')


async def void_func():
    return ''


class Message(Event):
    def __init__(self, js):
        super().__init__()
        self.args = None
        self.sender = js.get('sender')
        self.time = js.get('time')
        self.self_id = js.get('self_id')
        self.message_id = js.get('message_id')
        self.user_id = js.get('user_id')
        self.message = js.get('raw_message')
        self.text = re.sub(r'\[CQ:(.*?)\]', '', js['raw_message'])
        self.isGroup = js['message_type'] == 'group'
        self.at_me = f'[CQ:at,qq={js["self_id"]}]' in js['message']

    def __str__(self):
        return self.message

    def split(self, split_text=' '):
        msg = self.message.strip().split(split_text)
        return msg[0], msg[1:]

    def limit(person=True, group=True, at=False, both=False):
        def check_person(user_id):
            if person is True:
                return True
            elif isinstance(person, int):
                if person > 0 and user_id == person:
                    return True
                elif person < 0 and not user_id == -person:
                    return True
            elif isinstance(person, (list, tuple)):
                if len(person) == 0:
                    return False
                if person[0] > 0:
                    for i in person:
                        if user_id == i:
                            return True
                elif person[0] < 0:
                    for i in person:
                        if user_id == -i:
                            return False
                    return True

        def lim(func):
            @wraps(func)
            def wrapped_function(self):
                if self.isGroup:
                    if at and not self.at_me:
                        return void_func()
                    if both and not check_person(self.user_id):
                        return void_func()
                    if group is True:
                        return func(self)
                    elif isinstance(group, int):
                        if group > 0 and self.group_id == group:
                            return func(self)
                        elif group < 0 and not self.group_id == -group:
                            return func(self)
                        else:
                            return void_func()
                    elif isinstance(group, (list, tuple)):
                        if len(group) == 0:
                            return void_func()
                        if group[0] > 0:
                            for i in group:
                                if self.group_id == i:
                                    return func(self)
                        elif group[0] < 0:
                            for i in group:
                                if self.group_id == -i:
                                    return void_func()
                            return func(self)
                        else:
                            return void_func()
                else:
                    return func(self) if check_person(self.user_id) else void_func()
            return wrapped_function
        return lim

    def on_command(need=None):
        def check(func):
            @wraps(func)
            def wrapped_function(self):
                command, args = self.split()
                if need == command or not need:
                    self.args = args
                    return func(self)
                else:
                    return void_func()
            return wrapped_function
        return check


class PrivateMessage(Message):
    def __init__(self, js):
        super().__init__(js)


class GroupMessage(Message):
    def __init__(self, js):
        super().__init__(js)
        if 'group_id' in js:
            self.group_id = js['group_id']


def get_event_from_msg(msg: str):
    js = loads(msg)
    pt = js.get('post_type')
    if pt == 'message':
        if js['message_type'] == 'private':
            return PrivateMessage(js)
        elif js['message_type'] == 'group':
            return GroupMessage(js)
    elif pt == 'meta_event':
        return Mate(js)
