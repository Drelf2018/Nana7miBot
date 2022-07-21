class User:
    '''
    id	            string	用户的 id
    username	    string	用户的名称
    nickname	    string	用户在当前服务器的昵称
    identify_num	string	用户名的认证数字，用户名正常为：user_name#identify_num
    online	        boolean	当前是否在线
    bot	            boolean	是否为机器人
    status	        int	    用户的状态, 0 和 1 代表正常，10 代表被封禁
    avatar      	string	用户的头像的 url 地址
    vip_avatar	    string	vip 用户的头像的 url 地址，可能为 gif 动图
    mobile_verified	boolean	是否手机号已验证
    roles	        Array	用户在当前服务器中的角色 id 组成的列表
    '''
    def __init__(self, userInfo):
        self.id = userInfo.get('id')
        self.username = userInfo.get('username')
        self.nickname = userInfo.get('nickname')
        self.identify_num = userInfo.get('identify_num')
        self.online = userInfo.get('online')
        self.bot = userInfo.get('bot')
        self.status = userInfo.get('status')
        self.avatar = userInfo.get('avatar')
        self.vip_avatar = userInfo.get('vip_avatar')
        self.mobile_verified = userInfo.get('mobile_verified')
        self.roles = userInfo.get('roles')

    def __str__(self):
        return self.nickname

    def get_full_info(self):
        info = '[在线]' if self.online else '[离线]'
        if self.roles:
            info += str(self.roles)
        info += '机器人' if self.bot else '用户'
        info += f' {self.nickname}({self.username}#{self.identify_num},{self.id})'
        return info
