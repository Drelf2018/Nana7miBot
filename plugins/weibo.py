﻿import os
import httpx
from nana7mi import get_driver, log
from nana7mi.adapters.event import Message
from nana7mi.adapters.cqbot import cqBot
from yaml import Loader, dump, load

from plugins.weibo_detector.d2p import create_new_img
from plugins.weibo_detector.weiboSpider import get_data, get_detail, get_post, get_userInfo, get_comments

# 获取 cqBot 适配器
bot = get_driver()
cb: cqBot = bot.cqbot

# 读取已保存配置文件（博文、评论等）
FILEDIR = os.path.dirname(__file__)
with open(f'{FILEDIR}/weibo_detector/content.yml', 'r', encoding='utf-8') as fp:
    Content = load(fp, Loader=Loader)
    if not Content:
        Content = dict()

def save():
    with open(f'{FILEDIR}/weibo_detector/content.yml', 'w', encoding='utf-8') as fp:
        dump(Content, fp, allow_unicode=True)

# weibo.cn COOKIES
headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
    'cookie': '_T_WM=ceb8107a09ffde92303c2600aafcea3e; SUB=_2A25P9OE_DeRhGeFM7lQU8i7PyjmIHXVtFo93rDV6PUJbktAKLVrskW1NQNxRT3IFuL3bXA569DreXZlw2TSGQXb_; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWsM7qnLH5XXeUsRC8WX5b75NHD95QNeo-cSKz7e02fWs4DqcjPi--RiKnXiKnci--4i-zEi-2ReKzpe0nt; SSOLoginState=1659933039'
}

async def weibo(uid):
    log.debug(f'正在更新用户 {uid} 微博', 'Weibo')
    async with httpx.AsyncClient(headers=headers) as session:
        try:
            data = await get_data(session, uid)
            userInfo = dict()
        except Exception as e:
            log.error(f'更新用户 {uid} 微博失败 {e}', 'Weibo')
            return

        for i in range(1, 4):  # 爬取前 3 条
            try:
                post = await get_post(session, data, i)
            except Exception as e:
                log.error(f'爬取用户 {uid} 第 {i} 条微博失败 {e}', 'Weibo')
                continue

            # 检测微博是否存在或者是否发生变化
            rtext = post['repo'][0] if post.get('repo') else post.get('text', [[]])[0]
            if Content.get(post['mid'], {}).get('content') != rtext:

                # 生成图片并发送动态
                log.info(f'用户 {uid} 微博 {post["mid"]} 搬运中', 'Weibo')
                
                # 更新内容
                post = await get_detail(session, post)

                # 获取博主信息
                if not userInfo:
                    try:
                        userInfo = await get_userInfo(session, uid)
                    except Exception as e:
                        log.error(f'爬取用户 {uid} 信息失败 {e}', 'Weibo')

                # 文字版
                msg = '{name}\n粉丝 {follower} | 关注 {follow}\n发送了微博:\n'.format_map(userInfo)
                if post.get('repo'):
                    msg += '\n' + ''.join(post["repo"][0]) + '\n----------'
                msg += '\n' + ''.join(post["text"][0]) + '\n\n' + post['time']

                await cb.send_guild_msg(76861801659641160, 9638022, msg)
                
                # 图片版
                try:
                    image = await create_new_img(post, userInfo)
                    image.save(cb.PATH + '/data/images/wb/'+post['mid']+'.png')
                    img_text = '[CQ:image,file=wb/{mid}.png]'.format_map(post)
                except Exception as e:
                    img_text = str(e)
                await cb.send_guild_msg(76861801659641160, 9638022, img_text)

                # 发生变化保存到文件
                Content[post['mid']] = {'content': rtext, 'comment': Content.get(post['mid'], {}).get('comment', list())}
                save()
            
            # 爬最新一条微博的最新评论 本来想用的 但是频繁了 爬不到数据了
            elif i==1 and uid == 7198559139:
                cmt = await get_comments(session, post["mid"])
                old = set(Content[post['mid']].get('comment', set()))
                new = cmt.difference(old)
                if new:
                    log.info(f'用户 {uid} 微博 {post["mid"]} 评论 {new}', 'Weibo')
                    Content[post['mid']]['comment'] = list(old | cmt)
                    save()
                    for c in new:
                        await cb.send_guild_msg(76861801659641160, 9638022, c)

# 七海Nana7mi 微博监控
bot.sched.add_job(weibo, 'interval', seconds=10, next_run_time=bot.run_time(10), args=[7198559139])

# 响应来自 cqbot 的微博命令
@bot.setResponse(command='/weibo')
async def getWeibo(event: Message):
    async with httpx.AsyncClient(headers=headers) as session:
        data = await get_data(session, 7198559139)
        post = await get_post(session, data, 1)  
    return f'[CQ:image,file=wb/{post["mid"]}.png]'
