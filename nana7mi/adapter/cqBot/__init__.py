_private = '{\"action\": \"send_private_msg\", \"params\": {\"user_id\": %d, \"message\": \"%s\"}}'
_group = '{\"action\": \"send_group_msg\", \"params\": {\"group_id\": %d, \"message\": "\%s\"}}'
from .cqbot import cqBot
from .event import Mate, Message, Event, get_event_from_msg