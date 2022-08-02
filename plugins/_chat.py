import aiohttp
from nana7mi import get_bot
from nana7mi.adapters.cqBot import Message

bot = get_bot()

# 响应来自 cqbot 的一般消息命令
@bot.cqbot.setResponse(limit={'at': True})
async def chat(event: Message):
    bot.info(event, 'chat')
    url = 'http://api.qingyunke.com/api.php?'
    dic = {
        'key': 'free',
        'appid': 0,
        'msg': event.content
    }
    async with aiohttp.request('GET', url, params=dic) as resp:
        js = await resp.json(content_type='text/html', encoding='utf-8')
        msg = js['content'].replace('{br}', '\n')
    if not msg:
        msg = '我超 你在说些什么啊'
    if event.isGroup:
        msg = f'[CQ:at,qq={event.user_id}]' + msg
    bot.info(msg, 'chat')
    return event.reply(msg)

'''
@bot.sched.scheduled_job('interval', seconds=3, next_run_time=bot.run_time(2))
async def hello():
    await bot.cqbot.send_private_msg(3099665076, 'hello cqbot')'''