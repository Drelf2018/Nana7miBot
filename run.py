from nana7mi import cqBot, guildBot, get_bot

get_bot(
    cqbot=cqBot().load_buildin_plugins(), 
    guildbot=guildBot('stk')
).load_plugins('./plugins').run()