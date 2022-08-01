import asyncio
import base64
import json
import os
from io import BytesIO

import httpx
from lxml import etree
from PIL import Image

BASEPATH = os.path.dirname(__file__)
JSONPATH = os.path.join(BASEPATH, 'emoji.json')

if os.path.exists(JSONPATH):
    with open(JSONPATH, 'r', encoding='utf-8') as fp:
        js = json.load(fp)
else:
    js = {'url': 'https://emojixd.com', 'emoji': {}}
    resp = httpx.get('https://emojixd.com/list')
    html = etree.HTML(resp.text)
    for div in html.xpath('.//div[@class=\"col md-col-3 col-6\"]'):
        js['emoji'][div.xpath('./a/div[1]/text()')[0]] = div.xpath('./a/@href')[0]
    with open(JSONPATH, 'w', encoding='utf-8') as fp:
        json.dump(js, fp, indent=4, ensure_ascii=False)

Url: str = js['url']
Emoji: dict = js['emoji']

async def getEmojiImg(text: str) -> Image.Image:
    filepath = f'{BASEPATH}\\emoji{Emoji.get(text)}.png'
    if os.path.exists(filepath):
        return Image.open(filepath).convert('RGBA')
    async with httpx.AsyncClient() as session:
        resp = await session.get(Url+Emoji.get(text))
    html = etree.HTML(resp.content)
    src = html.xpath('.//tr[2]/td/img/@src')[0]
    data = base64.urlsafe_b64decode(src.replace('data:image/png;base64,', ''))
    img = Image.open(BytesIO(data)).convert('RGBA')
    img.save(filepath, 'png')
    return img


if __name__ == '__main__':
    asyncio.run(getEmojiImg('😎')).show()
