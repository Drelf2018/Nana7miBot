import re
import requests
from lxml import etree


# 请求
session = requests.session()

# weibo.cn COOKIES
headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
    'cookie': '_T_WM=2476121349a3d8c9baafccd04e173738; SUB=_2A25PkZ5NDeRhGeFM7lQU8i7PyjmIHXVtfSIFrDV6PUJbktCOLRbmkW1NQNxRTwggFvoPL-1_DHi8C53_T7KPuHtn; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWsM7qnLH5XXeUsRC8WX5b75NHD95QNeo-cSKz7e02fWs4DqcjPi--RiKnXiKnci--4i-zEi-2ReKzpe0nt; SSOLoginState=1653992990'
}


def get_userInfo(uid):
    # 获取博主当前信息
    resp = session.get(f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}', headers=headers)
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


def get_data(uid):
    resp = session.get(f'https://weibo.cn/u/{uid}', headers=headers)
    data = etree.HTML(resp.text.encode('utf-8'))
    return data


def get_post(data, n: int):
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
        return text.strip()

    # 博文过长 更换网址进行爬取
    murl = post.xpath('.//a[contains(text(), "全文")]/@href')
    if murl:
        resp = requests.get('https://weibo.cn'+murl[0], headers=headers)
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
        resp = requests.get(turl, headers=headers)
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


if __name__ == '__main__':
    data = get_data(7198559139)
    post = get_post(data, 1)
    # print(post)
