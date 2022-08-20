import os

from nana7mi import get_driver
from nana7mi.adapters import cqBot, guildBot

bot = get_driver()
bot.register_adapter(cqBot())
bot.register_adapter(guildBot('stk'))
bot.load_buildin_plugins().load_plugins('./plugins').run()
os.system("start " + __file__)
