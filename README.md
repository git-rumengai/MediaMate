# 项目介绍

MediaMate 是一个实验性的开源项目，利用playwright自动控制网页版多媒体账户，旨在自动化运营多媒体账号，我们的终极目标是让AI完全接管多媒体账号。

### 项目优点
1. 目前支持抖音和小红书两大平台，基本安装简洁方便。
2. 已实现功能包括自动**上传、下载、点赞、收藏、评论、@某人和消息回复**。
3. 多账户和多代理配置，方便同时运营多个账户。
4. 多媒体功能和AI功能完全隔离，如果只使用多媒体平台功能不需要复杂的安装依赖。
5. 通过 [302.AI](https://gpt302.saaslink.net/t2ohlA) (链接有优惠)接口，对接各种大模型，直接处理文本，图片，音乐，视频和搜索等各种问题。[参考文档](https://doc.302.ai/)
6. 通过MetaGPT设计Agent,增强内容生成能力。

### 项目缺陷
1. 没有处理自动化登录过程（也不打算处理），通过playwright保存登录信息，只有首次登录需要人工处理。
2. playwright模拟手动操作有天然缺陷，比如处理速度慢，以及网速对程序的正常执行影响很大。
3. 没有使用数据库，数据容易被误删。（项目初期不必要使用数据库）

### 快速开始
参考: [快速开始](docs/QuickStart.md)

# 安装

### 基础安装
可以自动化运营多媒体帐号
1. 安装playwright
```shell
    pip install playwright
    playwright install
```
2. 安装依赖
```shell
    pip install -r requirements.txt
```

### 高级安装(可选)

**MetaGPT**

通过MetaGPT构建Agent可以生成更复杂的内容。 （安装MetaGPT，建议通过源码安装）
1. clone项目
```shell
git clone https://github.com/geekan/MetaGPT
cd MetaGPT
```
2. 修改requirements.txt(可选)
注释掉大模型相关的工具包(OpenAI除外), 比如: anthropic, zhipuai, qianfan, volcengine
3. 安装
```shell
pip install --upgrade -e .
```
4. 运行demo时注释掉报错大模型相关代码(可选)

### 注意事项
1. 在任何地方导入metagpt之前都必须先导入项目配置，以确保metagpt输出的内容可以保存到项目指定目录
```python
from mediamate.config import config
```

**ffmpeg**

FFmpeg 是一个强大的多媒体处理工具包，能够用来处理音频和视频数据。它可以执行格式转换、视频剪辑、音频提取、视频流播放等任务。FFmpeg 支持几乎所有流行的音频、视频格式和编解码器。

1. 访问官网下载对应版本软件放到任意文件夹下
2. 将上述"任意文件夹"路径添加到环境变量中即可
3. 再cmd命令行输入"ffmpeg -version"可验证安装成功

# 配置
### 环境配置

环境配置填写在".env"文件中。所有配置以"MM__"开头，但是在程序使用中不需要前缀。
比如，环境变量中填写
```shell
MM__DATA=data
```
程序中使用：
```shell
config.get('DATA')
```
主要配置项目如下:
1. 数据保存目录：默认“data”目录
2. 固定代理：
3. 代理池：只支持快代理中的私密代理
4. 302AI：避免复杂的大模型配置，统一使用302AI接口，详细内容可访问：[302.AI](https://302.ai/)

### 多媒体账号配置
多媒体账户配置保存在".media.yaml"文件中，支持抖音和小红书的各种自定义操作配置。
内容比较细致，详见".media.template.yaml"。
正式使用时需要将".media.template.yaml"名称修改为".media.yaml"

# 文件目录
所有数据默认保存到"data"目录下，在"data"目录中还有几个子目录：

> 所有数据都会保存到对应的账户目录下

1. logs：保存程序运行过程中的日志信息
2. browser：保存所有账户浏览器数据，首次打开账户必须手动登录，登陆后的信息会被自动保存，如果该文件夹被删，下次打开账户需要重新登录。
3. upload：保存需要上传的图文或视频数据
4. download：保存所有下载的数据内容
5. agent：MetaGPT项目输出内容会默认保存到该目录

# 加入交流群(备注: ai)/项目赞助

| ![微信好友](docs/imgs/微信好友.jpg) |                 | ![二维码收款](docs/imgs/二维码收款.jpg) |
|:----------------------:|:----------------------:|:----------------------:|
| 微信好友        |                 | 二维码收款        |
