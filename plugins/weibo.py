import os
import asyncio

if __name__ != '__main__':
    from nana7mi import get_bot, CQ_PATH
    bot = get_bot()
    from plugins.weibo_detector.d2p import create_new_img
    from plugins.weibo_detector.weibo import get_data, get_post, get_userInfo, headers



async def weibo(uid):
    bot.info(f'正在更新用户 {uid} 微博', 'Weibo')
    try:
        data = get_data(uid)
        userInfo = dict()
    except Exception as e:
        bot.error(f'更新用户 {uid} 微博失败 {e}', 'Weibo')
        return

    for i in range(1, 5):
        # 爬取前4条
        try:
            post = get_post(data, i)
        except Exception as e:
            bot.error(f'爬取用户 {uid} 第 {i} 条微博失败 {e}', 'Weibo')
            continue
        pic_path = CQ_PATH + '/data/images/wb/'+post['mid']+'.png'
        if not os.path.exists(pic_path):
            # 如果不存在就生成图片并发送动态
            bot.info(f'用户 {uid} 微博 {post["mid"]} 搬运中', 'Weibo')

            # 保存图片
            if not userInfo:
                try:
                    userInfo = get_userInfo(uid)
                except Exception as e:
                    bot.error(f'爬取用户 {uid} 信息失败 {e}', 'Weibo')

            # 文字版
            msg = '{name}\n粉丝 {follower} | 关注 {follow}\n发送了微博:\n'.format_map(userInfo)
            if post['repo']:
                msg += '\n{repo}\n----------'.format_map(post)
            msg += '\n{text}\n\n{time}'.format_map(post)

            await bot.send_all_group_msg(msg, uid)
            
            # 图片版
            image = await create_new_img(post, userInfo, headers)
            image.save(pic_path, 'png')
            
            await bot.send_all_group_msg('[CQ:image,file=wb/{mid}.png]'.format_map(post), uid)
        # else:
        #     bot.info(f'用户 {uid} 微博 {post["mid"]} 已存在', 'Weibo')

# 七海Nana7mi 微博监控
bot.sched.add_job(weibo, 'interval', seconds=10, next_run_time=bot.run_time(10), args=[7198559139])
