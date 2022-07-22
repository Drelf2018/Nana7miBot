import json

import aiohttp
from nana7mi import get_bot

Headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}
bot = get_bot()
userdata = {}


def data_to_msg(key, old, new):
    if key == 'name':
        # 呀哒哟
        return f'用户名更新为：{new}'
    elif key == 'sex':
        return f'用户性别更新，旧：{old} 新：{new}'
    elif key == 'face':
        return f'用户头像更新\n旧头像：[CQ:image,file={old}]新头像：[CQ:image,file={new}]'
    elif key == 'birthday':
        return f'用户生日更新，旧：{old} 新：{new}'
    elif key == 'sign':
        return f'用户签名更新\n旧：{old}\n新：{new}'
    elif key == 'pendant' or key == 'nameplate':
        keyword = '装扮' if key == 'pendant' else '勋章'
        msg = f'用户{keyword}更新\n旧{keyword}：'
        if old.get('name'):
            msg += old['name'] + f'[CQ:image,file={old["image"]}]'
        else:
            msg += '空\n'
        msg += f'新{keyword}：'
        if new.get('name'):
            msg += new['name'] + f'[CQ:image,file={new["image"]}]'
        else:
            msg += '空'
        return msg
    elif key == 'fans_medal':
        msg = '用户粉丝牌更新\n'
        if not old['show'] == new['show']:
            msg += '是否展示：' + ('展示中' if old['show'] else '未展示') + ' -> ' + ('展示中\n' if new['show'] else '未展示\n')
        if not old['wear'] == new['wear']:
            msg += '是否佩戴：' + ('佩戴中' if old['wear'] else '未佩戴') + ' -> ' + ('佩戴中\n' if new['wear'] else '未佩戴\n')
        try:
            msg += '粉丝牌：' + old['medal']['medal_name'] + '|' + str(old['medal']['level']) + ' -> '
        except Exception:
            msg += '粉丝牌：空 -> '
        try:
            msg += new['medal']['medal_name'] + '|' + str(new['medal']['level'])
        except Exception:
            msg += '空'
        return msg + f'\nold:{old}\nnew:{new}'


@bot.sched.scheduled_job('interval', seconds=10, next_run_time=bot.run_time(12), args=[434334701])
async def bili(uid):
    try:
        async with aiohttp.ClientSession(headers=Headers) as session:
            r = await session.get(f'https://api.bilibili.com/x/space/acc/info?mid={uid}')
            if r.status == 200:
                js = await r.text()
                js = json.loads(js)
                if not js['code'] == -404:
                    u = js['data']
                    for key in ['name', 'sex', 'face', 'birthday', 'sign', 'pendant', 'nameplate', 'fans_medal']:
                        if not userdata.get(key):
                            if u.get(key):
                                userdata.update({key: u[key]})
                                bot.info(f'初始化 {key} 为 {u[key]}', 'BILI')
                        else:
                            if key in ['pendant', 'nameplate']:
                                if not userdata[key][key[0]+'id'] == u[key][key[0]+'id']:
                                    msg = userdata['name'] + ' ' + data_to_msg(key, userdata[key], u[key])
                                    userdata.update({key: u[key]})
                                    bot.info(msg, 'BILI')
                                    await bot.send_all_group_msg(msg, 'spider')
                            else:
                                if not userdata[key] == u[key]:
                                    msg = userdata['name'] + ' ' + data_to_msg(key, userdata[key], u[key])
                                    userdata.update({key: u[key]})
                                    bot.info(msg, 'BILI')
                                    await bot.send_all_group_msg(msg, 'spider')
        bot.info('资料更新完成', 'BILI')
    except Exception as e:
        bot.error(e, 'BILI')
