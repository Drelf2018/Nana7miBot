import asyncio
import json

import httpx
from nana7mi import get_driver, log
from nana7mi.adapters import cqBot
from nana7mi.adapters.event import Message

BASEURL = 'https://acrnm.com/?sort=default&filter=txt'
Products = dict()
bot = get_driver()
cb: cqBot = bot.cqbot

async def get_list(init=False):
    global Products
    new = httpx.get('http://aliyun.nana7mi.link/get_list', timeout=20.0).text
    new = json.loads(new)
    for name, val in new.items():
        msgs = name + '\n'
        if name not in Products:
            for p, li in val['price'].items():
                msgs += p + '\n'
                for color, size in li.items():
                    msgs += f'{color}: {size}\n'
        else:
            price = Products[name]["price"]
            for p, li in val['price'].items():
                if p in price:
                    flag = True
                    for color, size in li.items():
                        if price[p][color] != size:
                            if flag:
                                msgs += p + '\n'
                                flag = False
                            msgs += f'{color}: {size}\n'
                else:
                    msgs += p + '\n'
                    for color, size in li.items():
                        msgs += f'{color}: {size}\n'
        if not init and msgs != name + '\n':
            msgs = msgs.strip() + f'[CQ:image,file={val["img"]}]'
            log.info(msgs, 'acrnm')
            await cb.send_private_msg(2086378741, msgs)
    Products = new

@bot.sched.scheduled_job('interval', seconds=300, next_run_time=bot.run_time(30))
async def main():
    await get_list()
    log.info('更新完成', 'acrnm')

asyncio.run(get_list(init=True))

# # 响应来自 cqbot 的查询命令
# @bot.setResponse(command='/acrnm')
# async def acrnm(event: Message):
#     args = event.content.split()
#     match args[0]:
#         case 'list':
#             return event.reply(', '.join(list(Products.keys())))
#         case 'query':
#             pro = args[1]
#             return event.reply(', '.join(list(Products.get(pro, {}).get('option', set()))))
