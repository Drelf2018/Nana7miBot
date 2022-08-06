import re
import httpx
import asyncio
from lxml import etree

name_a = re.compile(r"<a href='https://m.weibo.cn/n/([\u4E00-\u9FA5A-Za-z0-9_]+)'>@(\1)</a>")
icon_span = re.compile(r'<span class="url-icon"><img alt="\[([\u4E00-\u9FA5A-Za-z0-9_]+)\]" src="([a-zA-z]+://[^\s]*)" style="width:1em; height:1em;" /></span>')

async def get_userInfo(session: httpx.AsyncClient, uid: int):
    # 获取博主当前信息
    resp = await session.get(f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}')
    data = resp.json()['data']['userInfo']
    userInfo = {
        'id': uid,
        'name': data['screen_name'],  # 昵称
        'face': data['toolbar_menus'][0]['userInfo']['avatar_hd'],  # 头像
        'desc': data['description'],  # 个性签名
        'follow': data['follow_count'],  # 关注数(str)
        'follower': data['followers_count']  # 粉丝数(str)
    }
    return userInfo


async def get_data(session: httpx.AsyncClient, uid: int):
    resp = await session.get(f'https://weibo.cn/u/{uid}')
    data = etree.HTML(resp.text.encode('utf-8'))
    return data


async def get_post(session: httpx.AsyncClient, data, n: int):
    """
    爬取指定位置博文
    Args:
        n (int) : 正数第 n 条博文 /*包含置顶博文*/
    Returns:
        博文信息
    """

    post = data.xpath('//div[@class="c"][{}]'.format(n))[0]
    repo = post.xpath('./div/span[@class="cmt" and contains(text(), "转发理由:")]/..')

    info = {
        'mid': post.xpath('.//@id')[0][2:],  # 这条博文的 mid 每条博文独一无二
        'repo': ''
    }

    if repo:
        repo = repo[0]
        info['repo'] = ''.join(repo.xpath('.//text()')).replace('\xa0', '').replace('&#13;', '\n')
        remove_text = ''.join(repo.xpath('./a[position()>last()-4]/text()')+repo.xpath('./span[last()]/text()'))
        remove_text = remove_text.replace('\xa0', '').replace('&#13;', '\n')
        info['repo'] = info['repo'].replace(remove_text, '').replace('转发理由:', '')

    def get_content_text(span):
        text = etree.tostring(span, encoding='utf-8').decode('utf-8')
        for _img in span.xpath('./span[@class="url-icon"]/img'):
            alt, src = _img.xpath('./@alt')[0], _img.xpath('./@src')[0]
            text = text.replace(
                f'<span class="url-icon"><img alt="{alt}" src="{src}" style="width:1em; height:1em;" /></span>',
                f'[{src}]'
            )
        for _a in span.xpath('.//a'):
            href = _a.xpath('./@href')[0].replace('&', '&amp;')
            atext = _a.xpath('./text()')[0]
            text = text.replace(f'<a href="{href}">{atext}</a>', atext)
        text = text.replace('<br />', '\n').replace('<span class="ctt">', '').replace('</span>', '')
        text = text.replace('[开学季]', '[https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/72/2021_kaixueji_org.png]')
        text = text.replace('[融化]', '[https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/53/2022_melt_org.png]')
        text = text.replace('[哇]', 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/3d/2022_wow_org.png')
        text = text.replace('[苦涩]', 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/7e/2021_bitter_org.png')
        return text.strip()

    # 博文过长 更换网址进行爬取
    murl = post.xpath('.//a[contains(text(), "全文")]/@href')
    if murl:
        resp = await session.get('https://weibo.cn'+murl[0])
        data = etree.HTML(resp.text.encode('utf-8'))
        span = data.xpath('//div[@class="c" and @id="M_"]/div/span')[0]
        info['text'] = get_content_text(span)[1:]
        if info['repo']:
            info['text'] = f'转发了 {span.xpath("../a/text()")[0]} 的微博：\n' + info['text']
    else:
        span = post.xpath('./div/span[@class="ctt"]')[0]
        info['text'] = get_content_text(span)
        if info['repo']:
            info['text'] = ''.join(span.xpath('../span[@class="cmt"][1]//text()')) + '\n' + info['text']

    # 爬取博文中图片
    pics = re.findall(r'组图共\d张', '/'.join(post.xpath('.//text()')))
    if pics:
        info['text'] = info['text'][:-1]
        turl = post.xpath(f'.//a[contains(text(), "{pics[0]}")]/@href')[0]
        resp = await session.get(turl)
        data = etree.HTML(resp.text.encode('utf-8'))
        info['picUrls'] = [('https://weibo.cn/' + url) for url in data.xpath('.//a[contains(text(), "原图")]/@href')]
    else:
        opic = post.xpath('.//a[contains(text(), "原图")]/@href')
        if opic:
            info['picUrls'] = [opic[0]]
        else:
            info['picUrls'] = []

    # 将其他信息与博文正文分割
    info['time'] = post.xpath('./div/span[@class="ct"]/text()')[0]

    info['repo'] = info['repo'].replace('\xa0', '').replace('&#13;', '\n')
    info['text'] = info['text'].replace('\xa0', '').replace('&#13;', '\n')

    return info


async def get_comments(session: httpx.AsyncClient, mid: int):
    Data = set()
    url = f'https://m.weibo.cn/api/comments/show?id={mid}'
    page_url = 'https://m.weibo.cn/api/comments/show?id={mid}&page={page}'
    resp = await session.get(url)
    page_max_num = resp.json()['data']['max']

    pending = []
    for i in range(1, page_max_num):
        p_url = page_url.format(mid=mid, page=i)
        pending.append(asyncio.create_task(session.get(p_url)))

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for done_task in done:
            resp = await done_task
            data = resp.json()['data'].get('data')
            for d in data:
                username = d['user']['screen_name']
                comment = d['text']
                if username == '七海Nana7mi':
                    Data.add(username+': '+icon_span.sub(r'[\1]', name_a.sub(r'@\1', comment)))
    return Data


async def main():
    data = get_data(7198559139)
    post = get_post(data, 5)
    userInfo = get_userInfo(7198559139)
    from d2p import create_new_img
    img = await create_new_img(post, userInfo)
    img.show()

if __name__ == '__main__':
    asyncio.run(main())