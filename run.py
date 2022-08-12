import os

from nana7mi import cqBot, get_bot, guildBot

get_bot(
    cqbot=cqBot().load_buildin_plugins(), 
    guildbot=guildBot('stk')
).load_plugins('./plugins').run()
os.system("start " + __file__)
