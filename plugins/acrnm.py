import asyncio
from typing import Optional, Set, Tuple

import httpx
from lxml import etree
from nana7mi import get_driver, log
from nana7mi.adapters import cqBot
from nana7mi.adapters.event import Message

BASEURL = 'https://acrnm.com'
Cookies = 'cookies_accepted=eyJfcmFpbHMiOnsibWVzc2FnZSI6ImRISjFaUT09IiwiZXhwIjoiMjAyMi0xMC0yMlQxNzoxMjoyNC41MjhaIiwicHVyIjoiY29va2llLmNvb2tpZXNfYWNjZXB0ZWQifX0=--a10dc29d513c2aa856f3065cf9e8fc342c4b4b5b; shopping_cart=eyJfcmFpbHMiOnsibWVzc2FnZSI6IklsdGRJZz09IiwiZXhwIjoiMjAyMi0wOC0wM1QwOToxMToxNy43NzVaIiwicHVyIjoiY29va2llLnNob3BwaW5nX2NhcnQifX0=--633b9fd86b8ee58c5039e4683e8bddd2a409f656; _acronym_session_production=52FeG+wDv/eZEDhlnHIQ2MgbiS6CQk8xd4QNAsGqlmvg9UP3t3yonwiUC67E4BGE9HP3z4FBupokfxKSFWyHWg4N9P+V2s+RE9PvyXxS1ae5oOEgKhB7TvWWHV48X7rJsv9jhs9evjbGXVT5nQlifcyPS5pleBv66DWHWwIX1HqYA0ppaO9Wk4aoySONDFgXbTGiZQ05wTXrQmC7kPTEeTxj8mJ5uRBw3q3XpZk+oPrzgoEclzQ5NL95EvaHNUuZqfdUS6oGY6Yj3j8b4MeJQ6lucira+AlOcYZ3eyhJZ7wSaQ4WepIvLBQYSVyvHDjlhvwB/Q2c2gJsG1oFkecISOIahA==--dBb2CQvzAH5vqZWg--knF0y1Mcp1pTVnxfIPuDNw==; acr_window_height=722; acr_window_pixel_ratio=1.25; acr_window_width=851'
Products = dict()
bot = get_driver()
cb: cqBot = bot.bot_dict['cqBot']

async def get_list(session: httpx.AsyncClient(), init: bool = False):
    if init:
        async with httpx.AsyncClient() as session:
            resp = await session.get(BASEURL, timeout=250.0)
    else:
        resp = await session.get(BASEURL, timeout=250.0)

    data = etree.HTML(resp.content)
    for a in data.xpath('/html/body/div/div[2]/div/div/a'):
        name = a.xpath('./div[@class="name"]/text()')[0]
        if not Products.get(name):
            Products[name] = {'url': a.xpath('./@href')[0], 'option': set()}
            if not init:
                await cb.send_private_msg(2086378741, f'新增 {name} 项')


async def get_detail(session: httpx.AsyncClient(), name: str, val: dict) -> Tuple[str, Set[Optional[str]]]:
    try:
        resp = await session.get(BASEURL+val['url'], timeout=250.0)
        data = etree.HTML(resp.content)
        content = set(data.xpath('//*[@id="variety_id"]/option/text()'))
        if val['option']:
            if not val['option'] == content:
                msg = name + '\n'
                soldout = list(val['option'].difference(content))
                if soldout:
                    msg += '售罄：' + ', '.join(soldout) + '\n'
                new = list(content.difference(val['option']))
                if new:
                    msg += '上新：' + ', '.join(new) + '\n'
                await cb.send_private_msg(2086378741, msg.strip())
                log.info(msg.strip(), 'acrnm')
        val['option'] = content
    except Exception as e:
        log.error(f'{name} error: {e}', 'acrnm')


@bot.sched.scheduled_job('interval', seconds=300, next_run_time=bot.run_time(5))
async def main():
    loop = asyncio.get_event_loop()
    async with httpx.AsyncClient(headers={'cookie': Cookies, 'Connection': 'close'}, timeout=250.0) as session:
        for key, val in Products.items():
            loop.create_task(get_detail(session, key, val))
        loop.create_task(get_list(session))
        log.info('更新完成', 'acrnm')
        await asyncio.sleep(250)

asyncio.run(get_list(None, init=True))

# 响应来自 cqbot 的查询命令
@bot.setResponse(command='/acrnm')
async def acrnm(event: Message):
    args = event.content.split()
    match args[0]:
        case 'list':
            return event.reply(', '.join(list(Products.keys())))
        case 'query':
            pro = args[1]
            return event.reply(', '.join(list(Products.get(pro, {}).get('option', set()))))
