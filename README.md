# 项目介绍

MediaMate 是一个实验性的开源项目，利用playwright自动控制网页版多媒体账户，旨在自动化运营多媒体账号，我们的终极目标是让AI完全接管多媒体账号。

## 项目优点
### 极简安装
**基础功能：** 没有数据库，没有docker，除了必要的python工具包和playwright，无需任何依赖。同时提供了环境配置一键安装方式，不懂代码也可以开箱即用。

**高级功能：** 不需要下载本地大模型，直接使用302AI提供的文本，图片，音乐，视频和搜索等各种大模型API。

### 可视化界面
1. 复杂的配置文件通过可视化界面快速配置，无需代码
2. 项目提供的模板也可以通过可视化界面执行
3. **<span style="color:red">首次启动可视化界面需要先保存配置, 否则演示页面为空白<span>**

### 支持抖音和小红书两大平台
**基础功能：** 
- 自动保存本地登录信息
- 自动上传图片/视频
- 自动下载平台中的个人数据
- 自动下载指定用户的公开数据
- 自动点赞，收藏，关注，评论，@某人
- 自动回复评论，抖音可自动私聊
- 多账户和多代理配置
- 支持使用 [302.AI](https://gpt302.saaslink.net/t2ohlA) (链接有优惠)接口，[参考文档](https://doc.302.ai/)
- 利用AI自动跳过不感兴趣的视频
- 利用AI自动评论和回复评论
- 利用AI自动回复抖音私聊

**高级功能：** 
- 支持使用 [MetaGPT](https://github.com/geekan/MetaGPT) 构建Agent，[参考文档](https://docs.deepwisdom.ai/main/zh/guide/get_started/introduction.html)
- 基于模板自动生成新闻，图片等可直接上传平台的内容
- 基于模板可自动识别本地图片/视频，然后生成可直接上传平台的内容

## 项目缺陷
1. 没有处理自动化登录过程（也不打算处理），通过playwright保存登录信息，只有首次登录需要人工处理。
2. playwright模拟手动操作有天然缺陷，比如处理速度慢，以及网速对程序的正常执行影响很大。
3. 没有使用数据库，数据容易被误删。（项目初期不必要使用数据库）

## 快速开始

参考: [快速开始](docs/QuickStart.md)

参考: [配置详解](docs/ConfigGuide.md)

参考: [常见答疑](docs/FAQ.md)

# 安装

## 一键安装

**必看**: [配置详解](docs/ConfigGuide.md)

1. 下载项目到本地后解压 "autoenv.rar"
2. 双击"install_env.bat"自动安装python环境和playwright
3. 双击"run_ui.bat"自动运行"MediaMate/mediamate/start_ui.py"文件
> 注意事项: 首次启动后先执行"项目配置", 确保配置完成".env"和"xhs"/"dy"

## 代码安装

可以自动化运营多媒体帐号
1. 安装playwright
```shell
    pip install playwright
    playwright install chromium
```
2. 安装依赖
```shell
    pip install -r requirements.txt
```

## 进阶安装

**[MetaGPT](https://github.com/geekan/MetaGPT)**

通过[MetaGPT](https://github.com/geekan/MetaGPT)构建Agent可以生成更复杂的内容。 
（安装[MetaGPT](https://github.com/geekan/MetaGPT)，建议通过源码安装）
1. clone项目
```shell
git clone https://github.com/geekan/MetaGPT
cd MetaGPT
```
2. 修改requirements.txt(可选)：注释掉大模型相关的工具包(OpenAI除外), 比如: anthropic, zhipuai, qianfan, volcengine
3. 安装
```shell
pip install --upgrade -e .
```
4. 运行demo时注释掉报错大模型相关代码(可选)

> 注意事项
> 1. 为了确保metagpt输出的内容可以保存到本项目指定目录, 请在MetaGPT项目最顶层的"\__init\__.py"文件中添加如下代码
> ```python
> # metagpt/__init__.py
> from mediamate.config import config
> ```

**[ffmpeg](https://www.ffmpeg.org/download.html)**

FFmpeg 是一个强大的多媒体处理工具包，能够用来处理音频和视频数据。它可以执行格式转换、视频剪辑、音频提取、视频流播放等任务。FFmpeg 支持几乎所有流行的音频、视频格式和编解码器。

1. 访问[官网](https://www.ffmpeg.org/download.html)下载对应版本软件放到任意文件夹下
2. 将上述"任意文件夹"路径添加到环境变量中即可
3. 再cmd命令行输入"ffmpeg -version"可验证安装成功


# 配置
## 全局配置

全局配置填写在".env"文件中。所有配置以"MM__"开头，但是在程序使用中不需要前缀。
比如，.env中填写
```shell
MM__DATA=data
```
程序中使用：
```shell
config.get('DATA')
```
主要配置项目如下:
1. 数据保存目录：默认"data"目录
2. 固定代理：
3. 代理池：只支持快代理中的私密代理
4. 302AI：避免复杂的大模型配置，统一使用302AI接口，详细内容可访问：[302.AI](https://302.ai/)
5. 详见".template.env"，正式使用时建议从".template.env"中复制所需要的配置到".env"

## 多媒体账号配置
1. 多媒体账户配置保存在".media.yaml"文件中，支持抖音和小红书的各种自定义操作配置。
2. 详见".template.media.yaml"，正式使用时建议从".template.media.yaml"中复制所需要的配置到".media.yaml"

# 文件目录
所有数据默认保存到"data"目录下，在"data"目录中还有几个子目录：

> 所有数据都会保存到对应的账户目录下

1. logs：保存程序运行过程中的日志信息
2. browser：保存所有账户浏览器数据，首次打开账户必须手动登录，登陆后的信息会被自动保存。如果该文件夹被删，下次打开账户需要重新登录。
3. upload：保存需要上传的图文或视频数据
4. download：保存所有下载的数据内容
5. agent：MetaGPT项目输出内容会默认保存到该目录 
6. active: 项目运行过程中随时被修改的数据。比如：
- 当前使用的代理地址
- 当前账户已发表过的文件标识（避免文件重复上传）
- playwright运行记录

# 加入交流群(备注: ai)/项目赞助

| ![微信好友](docs/imgs/微信好友.jpg) |                 | ![二维码收款](docs/imgs/二维码收款.jpg) |
|:----------------------:|:----------------------:|:----------------------:|
| 微信好友        |                 | 二维码收款        |
