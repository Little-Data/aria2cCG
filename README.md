# aria2c 控制器

<img src="https://github.com/user-attachments/assets/686ba1dc-861d-471b-acd0-eed14d01124c" />

简单管理[aria2c](https://github.com/aria2/aria2)命令行程序的启动与停止

aria2c是一个开源的支持多种协议的多线程下载器，体积小而强大。由于是命令行程序，使用起来多有不变，本程序实现了简单的启动与停止功能，方便快速上手

# 简单介绍

由于是控制器，你必须要有aria2c程序才能使用，本软件不附带

`Aria2c程序路径`：aria2c程序位置（必须）

`配置文件路径`：aria2c配置文件`.conf`位置（必须）

`Web管理页面路径`：[AriaNg](https://github.com/mayswind/AriaNg)网页管理页面html文件位置，可以通过该页面管理下载任务

**日志窗口只是提供了简单显示，难免会出现问题，如果很有必要显示aria2c的输出，建议使用系统的命令提示符直接启动aria2c！**

该软件所说的“服务”不是指系统的服务(services)，软件将aria2c启动在子进程内，没有命令提示符窗口，后台运行

# 使用例子

1. 将[aria2c](https://github.com/aria2/aria2)命令行程序下载
2. 将[AriaNg](https://github.com/mayswind/AriaNg)下载
3. 编写`.conf`文件，名字随意，但文件后缀一定是`.conf`，下面给一个简单模板，更多可以自己搜索

```
# 下载目录
dir=F:\Software\aria2\xiazai

# 启用断点续传
continue=true

# RPC 设置
enable-rpc=true
rpc-listen-all=false
rpc-listen-port=1234   # 开放的端口号
rpc-secret=1234        # RPC密码

# 设置允许的 RPC 请求来源（CORS 控制）
rpc-allow-origin-all=true

# 最大连接数
max-concurrent-downloads=5
max-connection-per-server=16
split=16

# 会话文件
input-file=F:\Software\aria2\aria2.session
save-session=F:\Software\aria2\aria2.session
save-session-interval=60

# 允许同名文件覆盖旧文件
allow-overwrite=true
```

**注意：会话文件部分一定要先创建一个空的文件（txt也好什么后缀都行）再把文件路径填写，否则aria2c提示找不到文件，启动失败！**

**请根据情况自行修改，不要复制粘贴什么都不改，启动必失败！**

4. 将本程序[下载](https://github.com/Little-Data/aria2cCG/releases)
5. 建议将以上所有文件都放在同个文件夹

程序启动后，所有程序的配置均保存在`aria2cCG.ini`文件中

程序图标使用了 [jsupdater](https://icon-sets.iconify.design/arcticons/jsupdater)
