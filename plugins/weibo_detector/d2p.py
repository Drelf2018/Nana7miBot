import os
import qrcode
from math import ceil
from PIL import Image, ImageDraw, ImageFont
try:
    from .TextManager import TextManager, Font
except Exception:
    from TextManager import TextManager, Font


async def create_new_img(post: dict, userInfo: dict, w=1080) -> Image.Image:
    """
    根据微博博文生成图片
    Args:
        post (dict) : 博文信息
        userInfo(dict) : 博主信息
        w (int) : 生成图片的宽度
    Returns:
        PIL 类中的 Image 对象
    """

    # 定义字体
    font_type = 'live/HarmonyOS_Sans_SC_Regular.ttf'  # 'C:/Windows/Fonts/msyh.ttc'
    font_blod_type = 'C:/Windows/Fonts/msyhbd.ttc'
    font_song = 'C:/Windows/Fonts/simsun.ttc'
    name_font = ImageFont.truetype(font_blod_type, 100)
    text_font = ImageFont.truetype(font_type, 100)

    text_width = 0.8  # 一个系数之后会用到
    # 人为规定一行写 21 个字好看，测量这 21 个字的长度
    # 再根据设定图片宽度 w 乘预设系数 text_width 调整字号
    tw, th = text_font.getsize('我不动脑子随手一写就是标标准准的二十一个字')
    size = int(100*text_width*w/tw)
    text_font = ImageFont.truetype(font_type, size)
    
    content = list()
    repoText, apos = post.get('repo', ([], []))
    for i, rt in enumerate(repoText):
        if i in apos:
            content.append((rt, (235, 115, 64), size, Font.homo))
        else:
            content.append((rt, '#1D1D1F', size, Font.homo))
    content.append('#')
    postText, apos = post.get('text', ([], []))
    for i, pt in enumerate(postText):
        if i in apos:
            content.append((pt, (235, 115, 64), size, Font.homo))
        else:
            content.append((pt, '#1D1D1F', size, Font.homo))
    content.append('#')

    div = 2 if len(post.get('picUrls', [])) >= 6 else 1
    for pic in post.get('picUrls'):
        bg = Image.open(pic)
        bg = bg.convert('RGBA')  # 读取图片
        bg = bg.resize((int(text_width*w)//div, int(bg.height*text_width*w/bg.width)//div), Image.ANTIALIAS)  # 调整大小
        content.append(bg)

    # 测量 发送时间以及设备 文本的高宽
    url_font = ImageFont.truetype(font_type, int(75*text_width*w/tw))
    s = post['time']
    tw, th = url_font.getsize(s)

    # 新建底片用以书写内容
    im = (await TextManager().setContent(content)).paste(text_width*w)
    image = Image.new("RGB", (w, int(im.height+0.55*w+th)), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 背景发卡
    faka = Image.open(os.path.join(os.path.dirname(__file__), 'card.png'))
    a = Image.new('L', faka.size, 80)  # 透明度 80/255
    i0 = 0
    j0 = 0
    for i in range(i0, ceil(image.height/faka.height)+1, 3):
        for j in range(j0-i, ceil(image.width/faka.width)+1, 4):
            image.paste(faka, (j*faka.width, i*faka.height), mask=a)  # 把发卡贴在背景上

    # 左上角黑框
    draw.rectangle([(0.05*w, 0.28*w), (0.088*w, 0.318*w)], fill='black')
    draw.rectangle([(0.0595*w, 0.2895*w), (0.088*w, 0.318*w)], fill='white')

    # 粘贴文字
    image.paste(im, (int(0.1*w), int(0.315*w)), mask=im.getchannel('A'))

    # 写发送时间
    draw.text((0.95*w-tw, 0.35*w+im.height+15), s, '#bebebe', url_font)

    # 二维码区域背景
    draw.rectangle([(0, int(im.height+0.37*w+th)), (w, int(im.height+0.55*w+th))], fill='#f9f9f9')

    # 右下角黑框
    draw.rectangle([(0.912*w, 0.312*w+im.height), (0.95*w, 0.35*w+im.height)], fill='black')
    draw.rectangle([(0.912*w, 0.312*w+im.height), (0.9405*w, 0.3405*w+im.height)], fill='white')

    # 二维码
    url = 'https://m.weibo.com/' + str(userInfo['id']) + '/' + post['mid']
    draw.text((int(0.05*w), int(im.height+0.43*w+th)), '扫描二维码查看这条动态', '#666666', text_font)
    draw.text((int(0.05*w), int(im.height+0.48*w+th)), url, '#bebebe', url_font)
    qrimg = qrcode.make(url).resize((int(0.16*w), int(0.16*w)), Image.ANTIALIAS)
    image.paste(qrimg, (int(0.83*w), int(im.height+0.38*w+th)))

    # 头像
    face = Image.open(userInfo['face'])  # 读取图片
    a = Image.new('L', face.size, 0)  # 创建一个黑色背景的画布
    ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色圆形
    face = face.resize((int(0.15*w), int(0.15*w)), Image.ANTIALIAS)
    a = a.resize((int(0.15*w), int(0.15*w)), Image.ANTIALIAS)  # 用于把方形头像变圆
    image.paste(face, (int(0.05*w), int(0.05*w)), mask=a)  # 粘贴至背景

    # 名字
    nw, nh = name_font.getsize(userInfo['name'])
    name_font = ImageFont.truetype(font_blod_type, int(7.5*w/nh))
    draw.text((int(0.21*w), int(0.05*w)), userInfo['name'], '#343434', name_font)

    # 关注与粉丝数
    follow_font = ImageFont.truetype(font_type, int(3.75*w/nh))
    draw.text((int(0.21*w), int(0.14375*w)), '粉丝 {follower} | 关注 {follow}'.format_map(userInfo), '#bebebe', follow_font)

    # 博主个性签名
    desc_font = ImageFont.truetype(font_song, int(12*w/nh))
    draw.text((int(0.015*w), int(0.205*w)), '“', '#787878', desc_font)
    dw, dh = desc_font.getsize('“')
    draw.text((int(0.015*w+dw), int(0.225*w)), userInfo['desc'], '#666666', follow_font)

    return image
