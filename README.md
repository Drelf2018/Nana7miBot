<div align="center">

<img src="https://user-images.githubusercontent.com/41439182/185760079-a8f6c1ba-ebcf-40dd-b728-69dbf1978ede.png" width="250px" />

# Nana7miBot

_✨ 基于 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 以及 [OneBot](https://github.com/howmanybots/onebot/blob/master/README.md) 的 Python 机器人框架实现 ✨_  

</div>

## 部署

想要部署一个属于自己的机器人，可以参照 `run.py`。

```python
import os

from nana7mi import get_driver
from nana7mi.adapters import cqBot

# 获取一个唯一的机器人框架
bot = get_driver()

# 为框架添加内置 go-cqhttp 适配器
bot.register_adapter(cqBot, url='ws://127.0.0.1:2434', path='./go-cqhttp')

# 加载内置插件以及从指定文件夹导入插件并运行
bot.load_builtin_plugins().load_plugins('./plugins').run()

# 重启
os.system("start " + __file__)
```
**其中** `load_builtin_plugins()` 与 `load_plugins()` 均返回机器人自身，因此可以链式调用。

**注意** `bot.run()` 是一个阻塞函数，仅当内部出现错误或主动关闭后，才会运行下面的重启指令。

框架代码写的很简陋，随意翻阅应该能看懂，如果有不懂的欢迎提 [Issues](https://github.com/Drelf2018/Nana7miBot/issues)。
