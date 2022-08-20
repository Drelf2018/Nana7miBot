import time

from bilibili_api import user
from nana7mi import get_driver, log
from nana7mi.adapters.event import Message
from nana7mi.adapters.cqbot import cqBot

from plugins._live2pic import Live2Pic

bot = get_driver()

async def auto_pic(uid: int = 434334701, roomid: int = 21452505, sourceURL: bool = False):
    try:
        if uid != 434334701:
            roominfo = await user.User(uid).get_live_info()
            roomid = roominfo['live_room']['roomid']
        return await Live2Pic(uid=uid, roomid=roomid).makePic(sourceURL)
    except Exception as e:
        log.error(e, 'pic')
        return e

# 响应来自 cqbot 的场报命令
@bot.setResponse(command='/live')
async def response(event: Message):
    uid = event.args[0] if event.args else 434334701
    img = await auto_pic(uid, sourceURL='-source=matsuri' in event.args)
    if isinstance(img, Exception):
        return f'生成直播场报失败: {img}'
    else:
        bot = event._receiver
        if isinstance(bot, cqBot):
            tt = int(time.time())
            img.save(f'{bot.PATH}/data/images/live/{uid}_{tt}.png')
            return f'[CQ:image,file=live/{uid}_{tt}.png]'

# 响应来自 cqbot 的场报命令
@bot.setResponse(command='/pic')
async def notice(event: Message):
    return '场报指令已更改为: /live [uid]\nuid 可不填默认为 434334701'
