import asyncio
import re
from typing import Any, List, Dict

import httpx
import requests
from lxml import etree

name_a = re.compile(r"<a href='https://m.weibo.cn/n/([\u4E00-\u9FA5A-Za-z0-9_]+)'>@(\1)</a>")
icon_span = re.compile(r'<span class="url-icon"><img alt="\[([\u4E00-\u9FA5A-Za-z0-9_]+)\]" src="([a-zA-z]+://[^\s]*)" style="width:1em; height:1em;" /></span>')


class EzFP:
    def __init__(self, data: bytes): self.__data = data
    def read(self): return self.__data

async def get_userInfo(session: httpx.AsyncClient, uid: int):
    # 获取博主当前信息
    resp = await session.get(f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}')
    data = resp.json()['data']['userInfo']
    face = await session.get(data['toolbar_menus'][0]['userInfo']['avatar_hd'])  # 请求头像
    userInfo = {
        'id': uid,
        'name': data['screen_name'],  # 昵称
        'face': face,  # 头像
        'desc': data['description'],  # 个性签名
        'follow': data['follow_count'],  # 关注数(str)
        'follower': data['followers_count']  # 粉丝数(str)
    }
    return userInfo


async def get_data(session: httpx.AsyncClient, uid: int) -> etree._Element:
    resp = await session.get(f'https://weibo.cn/u/{uid}')
    return etree.HTML(resp.text.encode('utf-8'))


def get_content_text(span: etree._Element):
    '''获取纯净博文内容'''

    # 将表情替换为图片链接
    for _span in span.xpath('./span[@class="url-icon"]'):
        src = _span.xpath('./img/@src')[0]
        _span.insert(0, etree.HTML(f'<p>[{src}]</p>'))

    # 获取这个 span 的字符串形式 并去除 html 格式字符
    text: List[str] = [p.replace(u'\xa0', '').replace('&#13;', '\n') for p in span.xpath('.//text()')]

    # 去除可能存在的多余信息
    for sub in text:
        if sub.startswith(('赞[', '转发[', '评论[')) or sub == '收藏':
            text.remove(sub)

    # 记录所有 <a> 标签出现的位置
    apos: List[int] = [0]
    for _a in span.xpath('.//a/text()'):
        try:
            apos.append(text.index(_a, apos[-1]))
        except ValueError:
            ...
    else:
        apos.pop(0)
    return text, apos


async def get_post(session: httpx.AsyncClient, data: etree._Element, n: int):
    """
    爬取指定位置博文
    Args:
        n (int) : 正数第 n 条博文 `包含置顶博文`
    Returns:
        博文信息
    """

    post: etree._Element = data.xpath('//div[@class="c"][{}]'.format(n))[0]
    postInfo = {'mid': post.xpath('.//@id')[0][2:], 'post': post, 'picUrls': list(), 'Error': list()}

    # 判断是否为转发微博
    repo = post.xpath('./div/span[@class="cmt" and contains(text(), "转发理由:")]/..')
    if repo:
        a, b = get_content_text(repo[0])
        a[0] = a[0].replace(":", "：")
        postInfo['repo'] = a[:-1], b

    # 博文过长 更换网址进行爬取
    more_url = post.xpath('.//a[contains(text(), "全文")]/@href')
    if more_url:
        resp = await session.get('https://weibo.cn' + more_url[0])
        data = etree.HTML(resp.text.encode('utf-8'))
        span = data.xpath('//div[@class="c" and @id="M_"]/div/span')[0]
        postInfo['text'] = get_content_text(span)
        if repo:
            postInfo['text'] = ['转发了 ', '@'+span.xpath("../a/text()")[0], ' 的微博'] + postInfo['text'][0], [1] + [p+3 for p in postInfo['text'][1]]
    else:
        span = post.xpath('./div/span[@class="ctt"]')[0]
        postInfo['text'] = get_content_text(span)
        if repo:
            postInfo['text'] = ['转发了 ', '@'+span.xpath('../span[@class="cmt"][1]/a/text()')[0], ' 的微博：'] + postInfo['text'][0], [1] + [p+3 for p in postInfo['text'][1]]
    
    return postInfo


async def get_detail(session: httpx.AsyncClient, postInfo: Dict[str, Any]):
    '''获取博文具体内容'''
    
    # 爬取博文中图片
    post: etree._Element = postInfo['post']
    images_url: List[str] = post.xpath('./div/a[contains(text(), "组图共")]/@href')
    if images_url:
        resp = await session.get(images_url[0])
        data = etree.HTML(resp.text.encode('utf-8'))
        picUrls = [('https://weibo.cn/' + url) for url in data.xpath('.//a[contains(text(), "原图")]/@href')]
    else:
        origin_url = post.xpath('./div/a[contains(text(), "原图")]/@href')
        if origin_url:
            picUrls = [origin_url[0]]
        else:
            picUrls = []

    for pic in picUrls:
        try:
            for _ in range(3):
                resp = requests.get(pic, headers=session.headers)  # 请求图片
                if resp.status_code == 200:
                    break
            else:
                raise '图片访问失败'
            postInfo['picUrls'].append(EzFP(resp.content))
        except Exception as e:
            postInfo['Error'].append(pic)

    # 将其他信息与博文正文分割
    postInfo['time'] = post.xpath('./div/span[@class="ct"]/text()')[0]

    return postInfo


async def get_comments(session: httpx.AsyncClient, mid: int):
    Data = set()
    url = f'https://m.weibo.cn/api/comments/show?id={mid}'
    try:
        resp = await session.get(url)
    except Exception:
        return set()
    data: List[dict] = resp.json()['data'].get('data')
    for d in data:
        username = d['user']['screen_name']
        comment = d['text']
        if username == '七海Nana7mi':
            Data.add(username+': '+icon_span.sub(r'[\1]', name_a.sub(r'@\1', comment)))
    return Data


async def main():
    headers = {
        'Connection': 'keep-alive',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
        'cookie': '_T_WM=ceb8107a09ffde92303c2600aafcea3e; SUB=_2A25P9OE_DeRhGeFM7lQU8i7PyjmIHXVtFo93rDV6PUJbktAKLVrskW1NQNxRT3IFuL3bXA569DreXZlw2TSGQXb_; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWsM7qnLH5XXeUsRC8WX5b75NHD95QNeo-cSKz7e02fWs4DqcjPi--RiKnXiKnci--4i-zEi-2ReKzpe0nt; SSOLoginState=1659933039'
    }
    async with httpx.AsyncClient(headers=headers) as session:
        data = await get_data(session, 7198559139)
        post = await get_post(session, data, 1)
        post = await get_detail(session, post)
        userInfo = await get_userInfo(session, 7198559139)
        print(post)
        from d2p import create_new_img
        image = await create_new_img(post, userInfo)
        image.show()

if __name__ == '__main__':
    asyncio.run(main())
