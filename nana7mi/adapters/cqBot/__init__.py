_private = '{\"action\": \"send_private_msg\", \"params\": {\"user_id\": %d, \"message\": \"%s\"}}'
_group = '{\"action\": \"send_group_msg\", \"params\": {\"group_id\": %d, \"message\": \"%s\"}}'
_guild = '{\"action\": \"send_guild_channel_msg\", \"params\": {\"guild_id\": %s, \"channel_id\": %s, \"message\": \"%s\"}}'
obj2js = lambda obj: str(obj).replace('\\', '\\\\').replace('"', '\\"').replace('\\\\n', '\\n')

from functools import wraps
from .event import Event, Mate, Message, MessageType, get_event_from_msg

async def failed_return(msg: str = ''):
    return msg

def limit(
    white_user = list(),
    banned_user = list(),
    white_group = list(),
    banned_group = list(),
    white_channel = list(),
    banned_channel = list(),
    at_me=False,
    group_both_user=False,
    guild_both_user=False,
    callback: str = ''
):
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

    check_user = lambda user_id: check_event(white_user, banned_user, user_id)
    check_group = lambda group_id: check_event(white_group, banned_group, group_id)
    check_channel = lambda channel_id: check_event(white_channel, banned_channel, channel_id)

    def check(func):
        @wraps(func)
        def wrapped_function(event: Message):
            msg = event.reply(callback.format(user_id=event.user_id))
            match event.message_type:
                case MessageType.Private:
                    return func(event) if check_user(event.user_id) else failed_return(msg)
                case MessageType.Group:
                    if at_me and not event.at_me:
                        return failed_return(msg)
                    if group_both_user:
                        if not check_user(event.user_id):
                            return failed_return(msg)
                    return func(event) if check_group(event.group_id) else failed_return(msg)
                case MessageType.Guild:
                    if at_me and not event.at_me:
                        return failed_return(msg)
                    if guild_both_user:
                        if not check_user(event.user_id):
                            return failed_return(msg)
                    return func(event) if check_channel(event.channel_id) else failed_return(msg)
        return wrapped_function
    return check

def on_command(command=None):
    def check(func):
        @wraps(func)
        def wrapped_function(event: Message):
            if command:
                if (pos := len(command)) > len(str(event)):
                    return failed_return()
                elif str(event)[:pos] != command:
                    return failed_return()
            event.real_content = str(event).replace(command, '')
            return func(event)
        return wrapped_function
    return check

from .cqbot import cqBot, CQ_PATH