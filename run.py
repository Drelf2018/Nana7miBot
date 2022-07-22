from nana7mi import get_bot, cqBot
import asyncio
import httpx

bot = get_bot(cqbot=cqBot())

# 响应来自 cqbot 的回声命令
@bot.cqbot.setResponse(command='/echo')
async def echo(event):
    return event.reply(' '.join(event.args).replace('&#91;', '[').replace('&#93;', ']'))

# 响应来自 cqbot 的大图命令
@bot.cqbot.setResponse(command='/big')
async def big(event):
    return event.reply(' '.join(event.args).replace(',subType=0', '').replace('CQ:image', 'CQ:cardimage').replace('&#91;', '[').replace('&#93;', ']'))


class Online:
    url = "https://m.weibo.cn/api/container/getIndex?from=page_100808&mod[]=TAB%3Ffrom%3Dpage_100808&mod[]=TAB&containerid=1008081a127e1db26d4483eadf1d1dbe1a80c2_-_live"
    last_online_status = None

    async def online(self):
        async with httpx.AsyncClient() as session:
            resp = await session.get(self.url)
        js = resp.json()
        for key1 in js['data']['cards']:
            for key2 in key1['card_group']:
                if key2['card_type'] == "30":
                    return key2['desc1']
    
    async def check(self):
        try:
            msg = await self.online()
        except Exception:
            return
        if msg and msg != self.last_online_status:
            self.last_online_status = msg
            if msg == '微博在线了':
                await bot.send_all_group_msg('七海Nana7mi '+msg, id='online')
            elif msg == '刚刚在线了':
                await bot.send_all_group_msg('七海Nana7mi '+msg, id='online')
        bot.info(msg, 'online')


# 七海Nana7mi 微博上线监控
nana7mi_online = Online()
bot.sched.add_job(nana7mi_online.check, 'interval', next_run_time=bot.run_time(10), seconds=10)

bot.load_plugins('./plugins')
asyncio.run(bot.run())
