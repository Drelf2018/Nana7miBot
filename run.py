import os

from nana7mi import get_driver
from nana7mi.adapters import cqBot, guildBot

bot = get_driver()
bot.register_adapter(cqBot, url='ws://127.0.0.1:2434', path='./go-cqhttp')
bot.register_adapter(guildBot, BASEURL='http://localhost:8080', aid='stk')
bot.load_builtin_plugins().load_plugins('./plugins').run()
os.system("start " + __file__)
