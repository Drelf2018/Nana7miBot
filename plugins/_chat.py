import aiohttp
from nana7mi import get_driver, log
from nana7mi.adapters.event import Message, MessageType, ParseLimit

bot = get_driver()

# 响应来自 cqbot 的一般消息命令
@bot.setResponse(plt=ParseLimit(at_me=True))
async def chat(event: Message):
    log.info(event, 'chat')
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
    if event.message_type == MessageType.Group:
        msg = f'[CQ:at,qq={event.user_id}]' + msg
    log.info(msg, 'chat')
    return msg
