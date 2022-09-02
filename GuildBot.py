CHANNELS = {

}
# BOT
import io

import botpy
from botpy.types.message import Message

from bilibili_api import user

from plugins._live2pic import Live2Pic

CODE = open(__file__, 'r', encoding='utf-8').read()
CODE = CODE[CODE.find('# BOT'):]

def save():
    msg = 'CHANNELS = {\n' + ',\n'.join([f"\t'{k}': '{v}'" for k, v in CHANNELS.items()]) + '\n}\n' + CODE
    open(__file__, 'w', encoding='utf-8').write(msg)

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

            case '/push':
                CHANNELS[message.guild_id] = message.channel_id
                save()
                await self.api.post_message(channel_id=message.channel_id, content='将自动推送至此子频道', msg_id=message.id)
            
            case '/remove':
                channel = CHANNELS.pop(message.guild_id, 0)
                if channel == 0:
                    await self.api.post_message(channel_id=message.channel_id, content='未在本频道设置推送', msg_id=message.id)
                else:
                    await self.api.post_message(channel_id=message.channel_id, content='移除本频道自动推送', msg_id=message.id)
                    save()

            case '/help':
                notice = '''/push
管理员在子频道中使用此指令，机器人将来会自动推送消息至此子频道。每个频道仅可设置一个，新设置会自动替换旧设置。

/remove
管理员在任意子频道中使用此指令，机器人将来不再自动推送消息至本频道。

/live [uid: int]
频道成员在子频道使用此指令后，机器人将立即推送一次数据至此子频道。其中 uid 为参数，可不填，不填时默认为 434334701 。不保证所有参数都能获取到返回值。'''
                await self.api.post_message(channel_id=message.channel_id, content=notice, msg_id=message.id)

            case '/post':
                path = 'go-cqhttp\\data\\images\\live\\' + args[1]
                fp = open(path, 'rb').read()
                for channel in CHANNELS.values():
                    await self.api.post_message(channel_id=channel, file_image=fp, msg_id=message.id)

if __name__ == '__main__':
    bot = GuildBot(intents=botpy.Intents(public_guild_messages=True))
    bot.run(appid=..., token=...)
