import httpx
import asyncio
from lxml import etree
from nana7mi import get_driver, log
from nana7mi.adapters import cqBot
from nana7mi.adapters.event import Message

BASEURL = 'https://acrnm.com/?sort=default&filter=txt'
Products = dict()
bot = get_driver()
cb: cqBot = bot.cqbot

async def get_list(init=False):
    resp = httpx.get(BASEURL, timeout=250.0)
    data = etree.HTML(resp.text)
    new_products = dict()
    for tr in data.xpath('.//tbody/tr'):
        msgs = ""
        for td in tr.xpath('./td'):
            match tag := td.xpath("./@class")[0][39:-5]:
                case "title":
                    name = td.xpath('.//span/text()')[0]
                    msgs += name + '\n'
                    if name not in Products:
                        Products[name] = dict()
                        Products[name]["variant"] = dict()
                        Products[name]["price"] = dict()
                case "variant":
                    for span in td.xpath('./div/span'):
                        color = '/'.join(span.xpath("./div/span/text()"))
                        size = '/'.join(span.xpath("./span/text()"))       
                        Products[name][tag][color] = size
                case "price":
                    if val := td.xpath('.//span/text()'):
                        if val[0] not in Products[name][tag]:
                            msgs += f'{tag}: {val[0]}\n'
                            Products[name][tag][val[0]] = None
                        if Products[name][tag][val[0]] != Products[name]["variant"]:
                            Products[name][tag][val[0]] = Products[name]["variant"]
                            for c, s in Products[name]["variant"].items():
                                msgs += f'{c}: {s}\n'
                        Products[name]["variant"] = dict()
                case _:
                    if val := td.xpath('.//span/text()'):
                        if Products[name].get(tag) != val[0]:
                            msgs += f'{tag}: {val[0]}\n'
                        Products[name][tag] = val[0]
        if msgs != name + '\n': new_products[name] = msgs
    
    if init: return

    if new_products: imgs = etree.HTML(httpx.get("https://acrnm.com/").text)
    for name, msgs in new_products.items():
        try:
            img = "https://acrnm.com/" + imgs.xpath(f'.//span[text()="{name}"]/../img/@src')[0]
            msgs = msgs.strip() + f'[CQ:image,file={img}]'
        except:
            ...
        log.info(msgs, 'acrnm')
        await cb.send_private_msg(2086378741, msgs)

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
