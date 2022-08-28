from .logger import log
from .nana7mi import Nana7mi
from .adapters.event import Message, MessageType, ParseLimit

__THE_ONLY_ONE_BOT = Nana7mi()

def get_driver():
    return __THE_ONLY_ONE_BOT
