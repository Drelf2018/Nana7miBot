﻿import time

from bilibili_api import live
from nana7mi import CQ_PATH, get_bot
from nana7mi.adapter.cqBot.event import Message

from plugins._live2pic import Live2Pic

bot = get_bot()
name = '七海Nana7mi'
uid = 434334701
room_id = 21452505
liveroom = live.LiveDanmaku(room_id)  # 接收弹幕, debug=True

async def auto_pic():
    try:
        image = await Live2Pic().makePic()
        tt = time.time()
        image.save(f'{CQ_PATH}/data/images/live/{tt}.png')
        return tt
    except Exception as e:
        bot.error(e, 'pic')
        return False


# 响应来自 cqbot 的场报命令
@bot.cqbot.setResponse(command='/pic')
async def response(event: Message):
    tid = await auto_pic()
    if tid:
        return event.reply(f'[CQ:image,file=live/{tid}.png]')
    else:
        return event.reply('生成直播场报失败')


# 下播/闲置中
@liveroom.on('PREPARING')
async def preparing(event):
    # await bot.send_all_group_msg(name+' 下播了\n正在生成场报，请稍后')
    tid = await auto_pic()
    if tid:
        await bot.send_all_group_msg(f'[CQ:image,file=live/{tid}.png]', id='live')
    else:
        await bot.send_all_group_msg('生成直播场报失败', id='live')


start_time: int = 0

# 开播/直播中
@liveroom.on('LIVE')
async def send_live_info(event):
    global start_time
    tt = time.time()
    if tt - start_time > 300:
        start_time = tt
        room = live.LiveRoom(room_id)
        info = await room.get_room_info()
        name = info['anchor_info']['base_info']['uname']
        title = info['room_info']['title']
        area = info['room_info']['area_name']
        cover = info['room_info']['cover']
        await bot.send_all_group_msg(f'{name} 正在 {area} 分区直播\n标题：{title}[CQ:image,file={cover}]', id='live')


# 重启监听
@bot.sched.scheduled_job('interval', id='reconnection', hours=1, next_run_time=bot.run_time(0)) 
async def reconnection():
    try:
        await liveroom.disconnect()
    except Exception:
        ...
    await liveroom.connect()