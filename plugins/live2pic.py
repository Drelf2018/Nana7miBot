import time

from bilibili_api import user
from nana7mi import get_driver, log
from nana7mi.adapters.event import Message
from nana7mi.adapters.cqbot import cqBot

from plugins._live2pic import Live2Pic

bot = get_driver()
cb: cqBot = bot.cqbot

# 响应来自 cqbot 的场报命令
@bot.setResponse(command='/live')
async def response(event: Message):
    uid = event.args[0] if event.args else 434334701
    try:
        if uid != 434334701:
            roominfo = await user.User(uid).get_live_info()
            roomid = roominfo['live_room']['roomid']
        else:
            roomid = 21452505
        img = await Live2Pic(uid=uid, roomid=roomid).makePic()

        tt = int(time.time())
        img.save(f'{cb.PATH}/data/images/live/{uid}_{tt}.png')
        return f'[CQ:image,file=live/{uid}_{tt}.png]'
    except Exception as e:
        log.error(e, 'pic')
        return f'生成直播场报失败: {e}'

# 响应来自 cqbot 的场报命令
@bot.setResponse(command='/pic')
async def notice(event: Message):
    return '场报指令已更改为: /live [uid]\nuid 可不填默认为 434334701'
