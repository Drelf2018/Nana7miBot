_private = '{\"action\": \"send_private_msg\", \"params\": {\"user_id\": %d, \"message\": \"%s\"}}'
_group = '{\"action\": \"send_group_msg\", \"params\": {\"group_id\": %d, \"message\": \"%s\"}}'
_guild = '{\"action\": \"send_guild_channel_msg\", \"params\": {\"guild_id\": %s, \"channel_id\": %s, \"message\": \"%s\"}}'


async def void_async_func():
    return ''

def limit(
    white_channel = list(),
    banned_channel = list(),
    white_group = list(),
    banned_group = list(),
    white_user = list(),
    banned_user = list(),
    at_me=False,
    channel_both_user=False,
    group_both_user=False
):
    def check_event(white: list, banned: list, eid: int) -> bool:
        if white:
            if eid in white:
                return True
        elif banned:
            if eid not in banned:
                return True
        else:
            return True
        return False

    check_user = lambda user_id: check_event(white_user, banned_user, user_id)
    check_group = lambda group_id: check_event(white_group, banned_group, group_id)
    check_channel = lambda channel_id: check_event(white_channel, banned_channel, channel_id)

    def check(func):
        @wraps(func)
        def wrapped_function(event: Message):
            match event.message_type:
                case MessageType.Private:
                    return func(event) if check_user(event.user_id) else void_async_func()
                case MessageType.Group:
                    if at_me and not event.at_me:
                        return void_async_func()
                    if group_both_user:
                        if not check_user(event.user_id):
                            return void_async_func()
                    return func(event) if check_group(event.group_id) else void_async_func()
                case MessageType.Guild:
                    if at_me and not event.at_me:
                        return void_async_func()
                    if channel_both_user:
                        if not check_user(event.user_id):
                            return void_async_func()
                    return func(event) if check_channel(event.channel_id) else void_async_func()
        return wrapped_function
    return check

def on_command(command=None):
    def check(func):
        @wraps(func)
        def wrapped_function(event: Message):
            if command:
                if (pos := len(command)) > len(str(event)):
                    return void_async_func()
                elif str(event)[:pos] != command:
                    return void_async_func()
            event.real_content = str(event).replace(command, '')
            return func(event)
        return wrapped_function
    return check

from functools import wraps
from .cqbot import cqBot
from .event import Event, Mate, Message, MessageType, get_event_from_msg