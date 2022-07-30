from re import I
from typing import List

from PIL import Image, ImageDraw
from PIL.ImageFont import truetype, FreeTypeFont


class Font:
    msyh = 'C:/Windows/Fonts/msyh.ttc'
    homo = 'live/HarmonyOS_Sans_SC_Regular.ttf'

    FontManager = {
        msyh: {16: truetype(msyh, 16)},
        homo: {16: truetype(homo, 16)}
    }

    @classmethod
    def getSizedFont(cls, font, size):
        if isinstance(font, FreeTypeFont):
            return font
        if not cls.FontManager.get(font):
            return None
        sizedFont = cls.FontManager[font].get(size)
        if sizedFont:
            return sizedFont
        else:
            newFont = truetype(font, size)
            cls.FontManager[font][size] = newFont
            return newFont


class TextManager:
    class Text:
        def __init__(self, text: str, color: str = '#FFFFFF', size: int = 16, font: Font = Font.homo) -> None:
            self.text = text
            self.color = color
            self.size = size
            self.font = Font.getSizedFont(font, size)
            self.width, self.height = self.sumSize()

        def __repr__(self) -> str:
            return f'[{self.text}]({self.color},{self.size},{self.font})'

        def __len__(self) -> int:
            return len(self.text)

        def getSize(self, pos: int = -1):
            return self.width[pos], self.height[pos]

        def getMaxPos(self, width: int, start: int = 0):
            start = self.width[start]
            for pos, w in enumerate(self.width):
                if w-start > width:
                    return pos - 1
            else:
                return pos

        def sumSize(self) -> List[int]:
            width, height = [0] * (len(self.text)+1), [0] * (len(self.text)+1)
            for i in range(len(self.text)+1):
                width[i], height[i] = self.font.getsize(self.text[:i])
            return width, height

    def __init__(self, content: list) -> None:
        self.setContent(content)

    def setContent(self, content) -> None:
        self.Content = []
        for c in content:
            if isinstance(c, tuple):
                text, *args = c
                last = 0
                now = 0
                while now < len(text):
                    if text[now] == '\n':
                        if last != now:
                            self.Content.append(self.Text(text[last:now], *args))
                        self.Content.append('#')
                        last = now + 1
                    now += 1
                else:
                    self.Content.append(self.Text(text[last:now], *args))
            else:
                self.Content.append(c)

    def print(self):
        for c in self.Content:
            print(c)

    def paste(self, limit: int):
        x, y, line_height = 0, 0, 3
        im = Image.new('RGBA', (int(limit), 1920), '#00000000')
        draw = ImageDraw.Draw(im)
        for c in self.Content:
            if c == '#':
                x = 0
                y += line_height
            elif isinstance(c, Image.Image):
                w, h = c.size
                if limit - x < w:
                    x = 0
                    y += line_height
                    line_height = 1.333 * h
                else:
                    line_height = max(line_height, 1.333 * h)

                im.paste(c, (x, y), mask=c.getchannel('A'))
                x += w
            elif isinstance(c, self.Text):
                pos = c.getMaxPos(limit-x)
                draw.text((x, y), c.text[:pos], c.color, c.font)
                w, h = c.getSize(pos)
                x += w
                line_height = max(line_height, 1.333 * h)
                while pos != len(c):
                    x = 0
                    y += line_height
                    line_height = 3
                    rpos = c.getMaxPos(limit, pos)

                    draw.text((x, y), c.text[pos:rpos], c.color, c.font)
                    w, h = c.getSize(rpos)
                    x += w - c.getSize(pos)[0]
                    line_height = max(line_height, 1.333 * h)
                    pos = rpos

        return im.crop((0, 0, limit, y+line_height))

tm = TextManager([
    ('1\n2\n\n3\n\n\nho\nmo\n来了', '#FF0000', 90, Font.homo),
    ('456', '#00FF00', 90, Font.homo),
    '#',
    ('二十一个字二十一个字二十一个字二十一哈哈了', '#0000FF', 90, Font.homo)
])
im = tm.paste(960)
bg = Image.new('RGB', im.size, '#FFFFFF')
bg.paste(im, mask=im.getchannel('A'))
bg.show()
