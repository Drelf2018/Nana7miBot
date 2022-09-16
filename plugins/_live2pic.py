import asyncio
import os
import time
from io import BytesIO
from random import choice
from typing import Optional, Tuple

import httpx
import jieba
import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from wordcloud import STOPWORDS, WordCloud
from yaml import Loader, load

matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.style.use("ggplot")
plt.rcParams['font.sans-serif'] = ['SimHei']
CODE = open(__file__, 'r', encoding='utf-8').readlines()


async def get_data_fig(dataMap: dict):
    fig, ax = plt.subplots(figsize=(12, 4))

    title = list(dataMap.keys())[::-1]
    follower = [d['follower'] for d in dataMap.values()][::-1]
    guardNum = [d['guardNum'] for d in dataMap.values()][::-1]

    delta = max(follower) - min(follower)
    text_delta = delta / 120

    delta2 = max(guardNum) - min(guardNum)
    alpha = delta / delta2 if delta2 else 1

    delta2 = int(min(guardNum) - delta2/6) if delta2 else min(guardNum)-delta/6

    delta = int(min(follower) - delta/6)

    ax.bar([i-0.2 for i in range(len(follower))], [i-delta for i in follower], width=0.4, color='#4ac2f6', bottom=delta, label='粉丝')
    ax.bar([i+0.2 for i in range(len(follower))], [alpha*(i-delta2) for i in guardNum], width=0.4, color='#617fe4', bottom=delta, label='舰长')
    
    for i in range(len(follower)):
        ax.annotate(
            text=str(follower[i]),  # 要添加的文本
            xy=(i-0.2, follower[i] + text_delta),  # 将文本添加到哪个位置
            fontsize=11,  # 标签大小
            color='#5AB1EF',  # 标签颜色
            ha="center",  # 水平对齐
            va="baseline"  # 垂直对齐
        )
        if i > 0:
            change = follower[i]-follower[i-1]
            ax.annotate(
                text=str(change),  # 要添加的文本
                xy=(i-0.2, follower[i] - text_delta),  # 将文本添加到哪个位置
                fontsize=11,  # 标签大小
                color='red' if change < 0 else 'green',  # 标签颜色
                ha="center",  # 水平对齐
                va="top"  # 垂直对齐
            )
    
    for i in range(len(guardNum)):
        ax.annotate(
            text=str(guardNum[i]),  # 要添加的文本
            xy=(i+0.2, delta+alpha*(guardNum[i]-delta2) + text_delta),  # 将文本添加到哪个位置
            fontsize=11,  # 标签大小
            color='#5AB1EF',  # 标签颜色
            ha="center",  # 水平对齐
            va="baseline"  # 垂直对齐
        )
        if i > 0:
            change = guardNum[i]-guardNum[i-1]
            ax.annotate(
                text=str(change),  # 要添加的文本
                xy=(i+0.2, delta+alpha*(guardNum[i]-delta2) - text_delta),  # 将文本添加到哪个位置
                fontsize=11,  # 标签大小
                color='red' if change < 0 else 'green',  # 标签颜色
                ha="center",  # 水平对齐
                va="top"  # 垂直对齐
            )

    ax.legend()
    ax.set_yticks([])
    plt.xticks(range(len(follower)), title)
    

    buf = BytesIO()
    fig.savefig(buf, transparent=True)
    buf.seek(0)
    img = Image.open(buf)
    return 'bar', img

async def word2pic(danmaku: list, folder: str='live/') -> Tuple[str, Image.Image]:
    # jieba 分词
    jieba.add_word('睡啄')
    word = [u['msg'] for u in danmaku if u['type'] == 'DANMU_MSG']
    word = jieba.cut('/'.join(word), cut_all=False)
    word = '/'.join(word)
    bg = Image.new('RGB', (1326, 500))
    graph = np.array(bg)

    # 停用词
    content = [line.strip() for line in open(folder+'stopwords.txt', 'r', encoding='utf-8').readlines()]
    stopwords = set(content) | STOPWORDS

    # 词云
    wc = WordCloud(
        font_path=folder+'HarmonyOS_Sans_SC_Regular.ttf',
        prefer_horizontal=1,
        collocations=False,
        background_color=None,
        mask=graph,
        stopwords=stopwords,  
        mode="RGBA")
    wc.generate(word)
    return 'wc', wc.to_image().resize((900, 900*bg.height//bg.width), Image.ANTIALIAS)

async def get_info(session: httpx.AsyncClient, url: str) -> Tuple[str, Tuple[dict, Image.Image]]:
    try:
        resp = await session.get(url, timeout=40.0)
    except Exception:
        resp = await session.get(url.replace('http://localhost:5762', 'https://api.nana7mi.link'), timeout=40.0)
    assert resp.status_code == 200
    liveinfo = resp.json()
    return 'info', liveinfo['live']


async def get_face(session: httpx.AsyncClient, uid: int = 434334701) -> Tuple[str, Tuple[Image.Image, Optional[Image.Image]]]:
    # 爬取装扮及头像
    resp = await session.get(f'https://account.bilibili.com/api/member/getCardByMid?mid={uid}', timeout=20.0)
    js = resp.json()
    # 头像
    if face := js.get('card', {}).get('face'):
        response = await session.get(face)  # 请求图片
        face = Image.open(BytesIO(response.read()))  # 读取图片
        w, h = face.size
        a = Image.new('L', face.size, 0)  # 创建一个黑色背景的画布
        ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色圆形

    # 装扮
    if pendant := js.get('card', {}).get('pendant', {}).get('image'):
        response = await session.get(pendant)  # 请求图片
        pendant = Image.open(BytesIO(response.read()))  # 读取图片
        pendant = pendant.convert('RGBA')

        bg = Image.new('RGBA', (int(1.75*w), int(1.75*h)), (0, 0, 0, 0))
        bg.paste(face, (int(0.375*w), int(0.375*h)), mask=a)  # 粘贴至背景
        pendant = pendant.resize((int(1.75*w), int(1.75*h)), Image.ANTIALIAS)  # 装扮应当是头像的1.75倍
        try:
            bg.paste(pendant, (0, 0), mask=pendant.getchannel('A'))  # 粘贴至背景
        except Exception:
            pendant = None
    # 粉圈
    if not pendant:
        image = Image.new('RGBA', (int(1.16*w), int(1.16*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.08*w), int(0.08*h)), mask=a)  # 粘贴至背景
        ps = Image.new("RGB", (int(1.16*w), int(1.16*h)), (242, 93, 142))
        a = Image.new('L', ps.size, 0)  # 创建一个黑色背景的画布
        ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色外圆
        ImageDraw.Draw(a).ellipse((int(0.06*w), int(0.06*h), int(1.1*w), int(1.1*h)), fill=0)  # 画黑色内圆
        image.paste(ps, (0, 0), mask=a)  # 粘贴至背景
        w, h = image.size
        bg = Image.new('RGBA', (int(1.25*w), int(1.25*h)), (0, 0, 0, 0))
        bg.paste(image, (int((1.25-1)/2*w), int((1.25-1)/2*h)))
    
    return 'face', bg.resize((150, 150), Image.ANTIALIAS)

def circle_corner(img: Image.Image, radii: int = 0) -> Image.Image:  # 把原图片变成圆角，这个函数是从网上找的
    """
    圆角处理
    :param img: 源图象。
    :param radii: 半径，如：30。
    :return: 返回一个圆角处理后的图象。
    """
    if radii == 0:
        radii = int(0.1*img.height)
    else:
        radii = int(radii)

    # 画圆（用于分离4个角）
    circle = Image.new('L', (radii * 2, radii * 2), 0)  # 创建一个黑色背景的画布
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 画白色圆形

    # 画4个角（将整圆分离为4个部分）
    w, h = img.size
    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角
    
    img = img.convert('RGBA')
    img.putalpha(alpha)

    return img


class Live2Pic:

    def __init__(self, folder: str = 'live/', uid: int = 434334701, roomid: int = 21452505):
        self.uid = uid
        self.roomid = roomid
        self.folder = folder
        self.liveinfo = dict()
        if os.path.exists(folder+f'{self.uid}\\bg.png'):
            self.bg = Image.open(folder+f'{self.uid}\\bg.png')
        else:
            self.bg = Image.open(folder+'bg.png')
        self.draw = ImageDraw.Draw(self.bg)
        self.font = {size: ImageFont.truetype(folder+'HarmonyOS_Sans_SC_Regular.ttf', size) for size in [28, 30, 32, 35]}
        self.fontbd = {size: ImageFont.truetype(folder+'HarmonyOS_Sans_SC_Bold.ttf', size) for size in [32, 40, 50]}
        self.text_color = '#1D1D1F'

    def paste(self, img: Image.Image, box: tuple):
        self.bg.paste(img, box, mask=img.getchannel('A'))

    async def makePic(self):
        # 主函数 用于生成图片

        Headers = {
            'Connection': 'keep-alive',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        }
        
        face: Image.Image = None
        face_count = 0

        async with httpx.AsyncClient(headers=Headers) as session:
            pending = [
                asyncio.create_task(get_info(session, f'http://localhost:5762/live/{self.roomid}/last')),
                asyncio.create_task(get_face(session, self.uid)),
            ]
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for done_task in done:
                    try:
                        code, data = await done_task  # 根据异步函数返回的 code 码执行相应 callback
                    except Exception as e:
                        print(e, done_task)
                        continue
                    match code:
                        case 'info':
                            self.liveinfo = data
                            pending.add(asyncio.create_task(get_data_fig(data['dataMap'])))
                            pending.add(asyncio.create_task(word2pic(data['danmaku'], self.folder)))
                        case 'face':
                            face = data
                        case 'wc':
                            self.paste(data, (90, 940))
                        case 'bar':
                            self.paste(data, (-75, 500))

        # 导入语录文件
        with open(f'{self.folder}quotations.yml', 'r', encoding='utf-8') as fp:
            quotations = load(fp, Loader=Loader)
            quotation = quotations.get(int(self.uid))

        t2s = lambda tt: time.strftime('%m/%d %H:%M', time.localtime(tt))
        self.draw.text((70, 178), '标题：'+self.liveinfo["title"], fill=self.text_color, font=self.fontbd[32])
        self.draw.text((70, 228), f'时间：{t2s(self.liveinfo["st"])} - {t2s(self.liveinfo["sp"])}', fill=self.text_color, font=self.font[28])
        self.draw.text((615, 1305), '*数据来源：api.nana7mi.link', fill='grey', font=self.font[30])
        if quotation:
            self.draw.text((140, 1440), choice(quotation), fill='grey', font=self.font[32])
        else:
            face_count += 1

        self.draw.text((70, 105), self.liveinfo['username']+' 直播记录', fill=self.text_color, font=self.fontbd[50])
        self.draw.text((70, 271), '基础数据', fill=self.text_color, font=self.fontbd[40])
        self.draw.text((70, 490), '趋势图表', fill=self.text_color, font=self.fontbd[40])
        self.draw.text((70, 885), '弹幕词云', fill=self.text_color, font=self.fontbd[40])

        total_income = self.liveinfo['send_gift'] + self.liveinfo['guard_buy'] + self.liveinfo['super_chat_message']

        basicData = [
            [('营收：', round(total_income, 2), self.text_color), ('弹幕：', self.liveinfo['total'], self.text_color), ('密度：', str(self.liveinfo['total']*60//(self.liveinfo['sp']-self.liveinfo['st']))+' / min', self.text_color)],
            [('礼物：', round(self.liveinfo['send_gift'], 2), (255, 168, 180)), ('航海：', round(self.liveinfo['guard_buy'], 2), (132, 212, 155)), ('醒目留言：', round(self.liveinfo['super_chat_message'], 2), (74, 194, 246))],
        ]

        for i, rows in enumerate(basicData):  # 写“基础数据”文字
            for j, data in enumerate(rows):
                self.draw.text((70+240*j, 329+51*i), data[0], fill=self.text_color, font=self.font[35])
                self.draw.text((70+240*j+35*len(data[0]), 329+51*i+4), str(data[1]), fill=data[2], font=self.font[32])

        income = Image.new('RGBA', (940, 50), (132, 212, 155) if self.liveinfo['guard_buy'] else 'grey')
        if total_income:
            income.paste((255, 168, 180), (0, 0, int(940*self.liveinfo['send_gift']/total_income), 50))
            income.paste((74, 194, 246), (int(940*(total_income-self.liveinfo['super_chat_message'])/total_income), 0, 940, 50))
        self.paste(circle_corner(income, 25), (70, 430))

        # 右上角立绘
        for root, folders, files in os.walk(f'{self.folder}{self.uid}'):
            nanami = Image.open(f'{self.folder}{self.uid}\\{choice(files)}')
            w = int(nanami.width*600/nanami.height)
            nanami = nanami.resize((w, 600), Image.ANTIALIAS)
            body = nanami.crop((0, 0, w, 400))  # 不是跟下半身切割了吗 上半身透明度保留

            a = body.getchannel('A')
            pix = a.load()
            for i in range(351, 400):
                for j in range(w):
                    pix[j, i] = int((8-0.02*i) * pix[j, i])  # 下半部分透明度线性降低

            self.bg.paste(body, (935-w//2, 20), mask=a)
            break
        else:
            face_count += 1

        # 左下角徽章
        for root, folders, files in os.walk(f'{self.folder}{self.uid}\\cards'):
            card = Image.open(f'{self.folder}{self.uid}\\cards\\{choice(files)}')
            card = card.resize((100, 100), Image.ANTIALIAS)
            card = card.convert('RGBA')
            self.bg.paste(card, (20, 1400), mask=card.getchannel('A'))
            break
        else:
            face_count += 1

        if face_count == 3:
            self.paste(face, (885, 95))
            self.bg = self.bg.crop((0, 46, 1080, 1416))
        else:
            self.paste(face, (910, 1375))

        return self.bg


if __name__ == '__main__':
    from bilibili_api import sync, user
    uid = 434334701
    roominfo = sync(user.User(uid).get_live_info())
    roomid = roominfo['live_room']['roomid']
    sync(Live2Pic(uid=uid, roomid=roomid).makePic()).show()
