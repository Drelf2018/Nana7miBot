import asyncio
from nana7mi import cqBot, get_bot

bot = get_bot(cqbot=cqBot())
# bot.load_buildin_plugins()
bot.load_plugins('./plugins')
asyncio.run(bot.run())
