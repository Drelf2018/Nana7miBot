import io

import botpy
from botpy.types.message import Message

from bilibili_api import user

from plugins._live2pic import Live2Pic

with open('channels.txt', 'r', encoding='utf-8') as fp:
    channels = fp.read().split(', ')
    while '' in channels:
        channels.remove('')

class GuildBot(botpy.Client):
    @property
    async def args(self):
        me = await self.api.me()
        content = self.event.content.replace(f'<@!{me["id"]}>', '')
        return content.strip().split()

    async def on_at_message_create(self, message: Message):
        self.event = message
        args = await self.args
        match args[0]:
            case '/live':
                if len(args) > 1 and args[1].isdigit():
                    uid = args[1]
                else:
                    uid = 434334701
                try:
                    if uid != 434334701:
                        roominfo = await user.User(uid).get_live_info()
                        roomid = roominfo['live_room']['roomid']
                    else:
                        roomid = 21452505
                    img = await Live2Pic(uid=uid, roomid=roomid).makePic()
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='png')
                    await self.api.post_message(channel_id=message.channel_id, file_image=img_byte_arr.getvalue(), msg_id=message.id)
                except Exception as e:
                    print(e, e.__traceback__.tb_lineno)
                    await self.api.post_message(channel_id=message.channel_id, content=f'生成场报时错误：{e}', msg_id=message.id)

            case '/livehere':
                if str(message.channel_id) not in channels:
                    channels.append(str(message.channel_id))
                    with open('channels.txt', 'w', encoding='utf-8') as fp:
                        fp.write(', '.join(channels))
            
            case '/post':
                path = 'go-cqhttp\\data\\images\\live\\' + args[1]
                fp = open(path, 'rb').read()
                for channel in channels:
                    await self.api.post_message(channel_id=channel, file_image=fp, msg_id=message.id)

if __name__ == '__main__':
    bot = GuildBot(intents=botpy.Intents(public_guild_messages=True))
    bot.run(appid=..., token=...)
