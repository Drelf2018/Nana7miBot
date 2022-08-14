import time

from bilibili_api import user
from nana7mi import CQ_PATH, get_bot
from nana7mi.adapters.cqBot import Message

from plugins._live2pic import Live2Pic

bot = get_bot()

async def auto_pic(uid: int = 434334701, roomid: int = 21452505, sourceURL: bool = False):
    try:
        if uid != 434334701:
            roominfo = await user.User(uid).get_live_info()
            roomid = roominfo['live_room']['roomid']
        image = await Live2Pic(uid=uid, roomid=roomid).makePic(sourceURL)
        tt = int(time.time())
        image.save(f'{CQ_PATH}/data/images/live/{uid}_{tt}.png')
        return tt
    except Exception as e:
        bot.error(e, 'pic')
        return e

# 响应来自 cqbot 的场报命令
@bot.cqbot.setResponse(command='/live')
async def response(event: Message):
    uid = event.args[0] if event.args else 434334701
    tid = await auto_pic(uid, sourceURL='-source=matsuri' in event.args)
    if isinstance(tid, int):
        return event.reply(f'[CQ:image,file=live/{uid}_{tid}.png]')
    else:
        return event.reply(f'生成直播场报失败: {tid}')

# 响应来自 cqbot 的场报命令
@bot.cqbot.setResponse(command='/pic')
async def notice(event: Message):
    return event.reply('场报指令已更改为: /live [uid]\nuid 可不填默认为 434334701')
