import time

from bilibili_api import live, user
from nana7mi import CQ_PATH, get_bot
from nana7mi.adapters.cqBot import Message

from plugins._live2pic import Live2Pic

bot = get_bot()
name = '七海Nana7mi'
uid = 434334701
room_id = 21452505
liveroom = live.LiveDanmaku(room_id)  # 接收弹幕, debug=True

async def auto_pic(uid: int = 434334701, roomid: int = 21452505):
    try:
        if uid != 434334701:
            roominfo = await user.User(uid).get_live_info()
            roomid = roominfo['live_room']['roomid']
        image = await Live2Pic(uid=uid, roomid=roomid).makePic()
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
    tid = await auto_pic(uid)
    if isinstance(tid, int):
        return event.reply(f'[CQ:image,file=live/{uid}_{tid}.png]')
    else:
        return event.reply(f'生成直播场报失败: {tid}')

# 响应来自 cqbot 的场报命令
@bot.cqbot.setResponse(command='/pic')
async def notice(event: Message):
    return event.reply('场报指令已更改为: /live [uid]\nuid 可不填默认为 434334701')


# 下播/闲置中
@liveroom.on('PREPARING')
async def preparing(event):
    # await bot.send_all_group_msg(name+' 下播了\n正在生成场报，请稍后')
    tid = await auto_pic()
    if isinstance(tid, int):
        await bot.cqbot.send_guild_msg(76861801659641160, 9638023, f'[CQ:image,file=live/434334701_{tid}.png]')
    else:
        await bot.cqbot.send_guild_msg(76861801659641160, 9638023, f'生成直播场报失败: {tid}')


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
        await bot.cqbot.send_guild_msg(76861801659641160, 9638023, f'{name} 正在 {area} 分区直播\n标题：{title}[CQ:image,file={cover}]')


# 重启监听
@bot.sched.scheduled_job('interval', id='reconnection', hours=1, next_run_time=bot.run_time(10)) 
async def reconnection():
    try:
        await liveroom.disconnect()
    except Exception:
        ...
    try:
        await liveroom.connect()
    except Exception as e:
        bot.error(f'连接直播间时错误: {e}', 'live')
