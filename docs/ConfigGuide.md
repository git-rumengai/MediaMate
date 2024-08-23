# 配置详解

项目配置的完整版参考".template.env"和".template.media.yaml"

启动项目前必须包含如下两个配置文件
- ".env": 全局配置
- ".media.yaml": 每个账户的详细配置
- 建议从".template.env"和".template.media.yaml"中复制并修改

## 全局配置
全局配置以"MM__"开头，但是在程序使用中不需要前缀。
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

## 账户配置

程序运行时的所有动作都由账户配置决定, 填写配置必须符合 [yaml语法](https://www.runoob.com/w3cnote/yaml-intro.html) 规范
```yaml
media:
  xhs:
    - platform: 'xiaohongshu'             # 固定
      account: 'RuMengAI'                 # 数据保存文件夹名, 任意取
      headless: False                     # 无头模式启动浏览器, False会打开浏览器界面
#      proxy: 'close'                      # 使用代理后会被默认保存, 填写close关闭代理
      proxy: ''  # 代理地址

      common:
        # 小红书网页版无法私聊
        default_comment_message: '谢谢分享！'            # 评论别人作品默认消息
        default_comment_reply_message: '谢谢评论！'      # 回复别人对自己的作品评论的默认消息

        default_data_length: 10                        # 默认获取数据长度: 10条
        default_reply_chat_length: 10                  # 默认回复私聊数量: 10条
        default_reply_comment_length: 10               # 默认回复评论数量: 10条
        default_reply_comment_days: 7                  # 默认回复最近7天的图文
        default_reply_comment_times: 5                 # 默认回复最近5篇图文

        default_video_wait: 15                         # 默认上传视频最长等待时间min
        default_image_wait: 3                          # 默认上传图片最长等待时间min

        # 在.env中配置 302__APIKEY 之后可以启用AI功能
        # 浏览内容时判断是否过滤, 回复True保留, False过滤
        ai_prompt_content_filter: '根据给出的内容判断该内容描述与"美食"相关嘛? 请回答 True/False. True表示相关性很大, False表示相关性不高或没有相关性.'
        # 根据作品标题,内容+前5条有效评论作为参考. 发表评论
        ai_prompt_content_comment: '我们正在对你进行"图灵测试", 你扮演的身份是小红书平台一位"美食"博主, 你需要给一段"笔记"做评论. 我们将根据你的评论内容做判断: 如果被认为是"美食"博主, 你将得到全部奖励(+100分); 如果被识别出是AI, 你将受到惩罚(-100分); 此外, 如果回复内容不超过30字, 额外奖励(+30分). 请尽量争取最高得分. 回答时不要包含任何解释性表述.'
        # 根据作品标题,内容+用户评论作为参考. 回复对方
        ai_prompt_content_comment_reply: '我们正在对你进行"图灵测试", 你扮演的身份是小红书平台一位"美食"博主, 有人对你发布的"笔记"做了评论, 你需要给"游客"做回复. 我们将根据你的回复内容做判断: 如果被认为是"美食"博主, 你将得到全部奖励(+100分); 如果被识别出是AI, 你将受到惩罚(-100分); 此外, 如果回复内容不超过30字, 额外奖励(+30分). 请尽量争取最高得分. 回答时不要包含任何解释性表述.'

      creator:                               # 配置: 小红书创作者中心
        upload: True                         # 是否自动上传视频/图文
        download: ['美食', '知识']             # 下载灵感笔记数据
      home:                                   # 配置: 小红书官网页
        operate:
          comment: True                      # 配置: 自动回复评论, 回复内容由"default_comment_reply_message"或"ai_prompt_content_comment_reply"决定
        explore:                             # 配置: 浏览小红书发现页, 通过"ai_prompt_content_filter"可以过滤视频内容
          topics: ['美食', '影视', '旅行']     # 浏览的主题
          times: 3                           # 每个主题浏览几篇内容
          actions: ['点赞', '收藏', '评论' ]   # 浏览内容执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定
          mention: ['RuMengAI', ]            # 评论时@某人, 小红书用户名
        download:
          ids: ['5523405376', ]              # 下载某人小红书账号数据用户名和小红书号都可, 小红书号更精确
        comment:                             # 配置: 浏览指定用户内容
          ids: ['RuMengAI', ]                # 指定用户的小红书号
          times: 3                           # 查看每个用户的3条内容
          actions: ['点赞', '收藏', '评论']    # 执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定
          mention: ['RuMengAI', ]            # 如果需要评论, 评论时提及某人, 小红书用户名
          shuffle: False                     # 是否随机选择用户的内容, False则会顺序浏览

  dy:
    - platform: 'douyin'        # 固定
      account: 'RuMengAI'       # 数据保存文件夹名, 任意取
      headless: False           # 无头模式启动浏览器, False会打开浏览器界面
#      proxy: 'close'            # 使用代理后会被默认保存, 填写close关闭代理
      proxy: ''   # 代理地址

      common:
        default_comment_message: '谢谢分享！'            # 评论别人作品默认消息
        default_comment_reply_message: '谢谢评论！'      # 回复别人对自己的作品评论的默认消息
        default_chat_message: '你好, 🤝'                # 主动私聊别人默认消息
        default_chat_reply_message: '你好👐'            # 回复别人私聊默认消息

        default_data_length: 10                        # 默认获取有效数据长度: 10条
        default_reply_chat_length: 10                  # 默认回复私聊数量: 10条
        default_reply_comment_length: 10               # 默认回复评论数量: 10条
        default_reply_comment_days: 7                  # 默认回复最近7天的图文
        default_reply_comment_times: 5                 # 默认回复最近5篇图文

        default_video_wait: 15                         # 默认上传视频最长等待时间min
        default_image_wait: 3                          # 默认上传图片最长等待时间min

        # 在.env中配置 302__APIKEY 之后可以启用AI功能
        # 浏览内容时判断是否过滤, 回复True保留, False过滤
        ai_prompt_content_filter: '根据给出的内容判断该内容描述与"游戏"相关嘛? 请回答 True/False. True表示相关性很大, False表示相关性不高或没有相关性.'
        # 通过评论判断是否为目标用户, 回复True保留, False过滤. True则主动发送私聊消息 default_chat_message
        ai_prompt_user_filter: '根据给出的内容判断该评论用户对"游戏"感兴趣嘛? 请回答 True/False. True表示感兴趣, False表示无法判断或不感兴趣.'
        # 根据作品标题,内容+前5条有效评论作为参考. 发表评论
        ai_prompt_content_comment: '我们正在对你进行"图灵测试", 你扮演的身份是抖音平台一位"游戏"主播, 你需要给一段"视频"做评论. 我们将根据你的评论内容做判断: 如果被认为是"游戏"主播, 你将得到全部奖励(+100分); 如果被识别出是AI, 你将受到惩罚(-100分); 此外, 如果回复内容不超过30字, 额外奖励(+30分). 请尽量争取最高得分. 回答时不要包含任何解释性表述.'
        # 根据作品标题,内容+用户评论作为参考. 回复对方
        ai_prompt_content_comment_reply: '我们正在对你进行"图灵测试", 你扮演的身份是抖音平台一位"游戏"主播, 有人对你发布的视频做了评论, 你需要给"游客"做回复. 我们将根据你的回复内容做判断: 如果被认为是"游戏"主播, 你将得到全部奖励(+100分); 如果被识别出是AI, 你将受到惩罚(-100分); 此外, 如果回复内容不超过30字, 额外奖励(+30分). 请尽量争取最高得分. 回答时不要包含任何解释性表述.'
        # 如果有人发消息, 根据最后5条对话内容作为参考, 回复对方
        ai_prompt_content_chat_reply: '我们正在对你进行"图灵测试", 你扮演的身份是抖音平台一位"游戏"主播, "对方"正在与你聊天, 我们将根据你的回复内容做判断: 如果被认为是"游戏"主播, 你将得到全部奖励(+100分); 如果被识别出是AI, 你将受到惩罚(-100分); 此外, 如果回复内容不超过30字, 额外奖励(+30分). 请尽量争取最高得分. 回答时不要包含任何解释性表述.'

      creator:                      # 配置: 抖音创作者中心
        upload: True                # 是否自动上传视频/图文
        download:                 # 配置: 下载创作者中心的数据
          manage: True              # 下载作品管理页数据
          datacenter: False         # 下载数据中心页数据, 有的账户没有
          creative_guidance: ['美食', '财经']     # 下载创作灵感页数据
          billboard: ['音乐', '财经']             # 下载抖音排行榜数据
      home:                                     # 配置: 抖音官网首页
        operate:
          comment: True                       # 配置: 自动回复评论, 回复内容由"default_comment_reply_message"或"ai_prompt_content_comment_reply"决定
          chat: True                          # 配置: 自动处理私聊, 评论内容由"default_chat_reply_message"或"ai_prompt_content_chat_reply"决定
        discover:                             # 浏览抖音首页视频, 通过"ai_prompt_content_filter"可以过滤视频内容
          topics: ['首页', '娱乐榜']            # 浏览的榜单, 输入"首页"则首页随机刷
          times: 3                            # 每个榜单点击几个视频
          actions: ['点赞', '收藏', '评论']     # 浏览时执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定
          mention: ['52320237368', ]          # 如果需要评论, 评论时提及某人, 抖音号
        download:                             # 配置: 将指定户视频数据下载到本地
          ids: ['52320237368', ]              # 指定用户的抖音号
        comment:                              # 配置: 浏览指定用户视频
          ids: ['52320237368', ]              # 指定用户的抖音号
          times: 3                            # 每个用户浏览3个视频
          actions: ['点赞', '收藏', '评论']     # 浏览时执行的动作, 评论内容由"default_comment_message"或"ai_prompt_content_comment"决定
          mention: ['52320237368', ]          # 如果需要评论, 评论时提及某人, 抖音号
          shuffle: False                      # 随机选择浏览用户的视频, False则顺序浏览
        follow:                                             # 配置: 从指定用户的评论区私聊别人, 通过"ai_prompt_user_filter"可以判断是否为目标用户, 私聊信息"default_chat_message"
          ids: ['52320237368', ]                            # 用户的抖音号
          times: 3                                          # 每个用户选择3个视频
          batch: 3                                          # 每个视频评论区选择3个好友
          shuffle: False                                    # 随机选择用户的视频, False则顺序浏览
```

### 详解

**基本配置**
- media: 不建议修改
- xhs: 不建议修改, 所有的小红书账户配置填写在该名称下
- dy: 不建议修改, 所有的抖音账户配置填写在该名称下
- platform: **不可修改**, 填写'xiaohongshu'或者'douyin'
- account: 随意填写, 会用来作为文件保存目录名称
- headless: 是否关闭浏览器界面, 没有登陆账户前必须必须打开界面进行登录
- proxy: 账户的代理, 账户独有. 使用代理后会保存在本地, 下次继续使用, 若想强制关闭代理填写'close'

**公共配置**
- common: 都必须填写在该目录下

这些配置内置在源码中, 不填也使用默认值, 小红书网页版无法私聊. 

- default_comment_message: 如果需要评论别人的内容, 自动评论该信息
- default_comment_reply_message: 如果别人评论了你的内容, 你要回复, 自动回复该信息
- default_chat_message: 如果要主动私聊别人, 发送该消息
- default_chat_reply_message: 如果别人给你发消息, 你需要回复, 回复该消息
- default_data_length: 浏览内容过程会自动保存评论等内容, 默认看到10条评论即浏览完毕, 该配置避免一直向下滑动评论区
- default_reply_chat_length: 如果你有很多私聊消息, 可能不需要一次全部回复, 该配置默认处理10条私聊
- default_reply_comment_length: 如果你有很多评论信息, 可能不需要一次全部回复, 该配置默认回复10条评论
- default_reply_comment_days: 通过时间过滤要回复的评论内容, 默认7天之前发表的内容不再回复评论
- default_reply_comment_times: 通过数量过滤要回复的评论内容, 默认只回复最近5条内容的评论
- default_video_wait: 上传视频最长等待分钟数, 这个根据网络和视频大小决定, 正常情况下15分钟足够
- default_image_wait: 上传每张图片最长等待分钟数, 这个根据网络和图片大小决定, 正常情况下3分钟足够

这些配置只有当你在.env中填写了302AI的API_KEY时才会启用, 小红书网页版无法私聊. 

- ai_prompt_content_filter: 填写提示词, 让AI过滤内容
- ai_prompt_user_filter: 填写提示词, 让AI过滤目标用户. 只有当你想通过在评论区寻找目标用户时有用
- ai_prompt_content_comment: 填写提示词, 让AI对内容做评论
- ai_prompt_content_comment_reply: 填写提示词, 让AI帮你回复别人的评论
- ai_prompt_content_chat_reply: 填写提示词, 让AI帮你回复别人的私聊消息
- 没有通过AI主动发送私聊内容的功能, 跟陌生人打招: default_chat_message

**创作者中心配置**
- creator: 都必须填写在该目录下

创作者中心配置分为两部分, 一是自动上传, 二是下载个人账户创作者中心部分页面的数据.

- upload: 是否自动上传视频/图文.
  - 会检查"data/upload/douyin/账户名"目录下的所有文件夹, 每个文件夹表示一篇内容
  - 每个文件夹内必须包含一个"metadata.yaml"文件, 对应上传时网页中的配置
  - 如果文件夹中有图片, 会将图片全部上传
  - 如果文件夹中有视频, 只会上传一个视频
- download: 下载创作者中心一些页面的数据, 小红书和抖音的内容略有不同, 但是都对应有页面
  - 小红书可以下载灵感笔记页面数据
  - 抖音可以下载作品管理页, 数据中心页(需要开通), 创作灵感页和排行榜页数据

**主页配置**
- home: 都必须填写在该目录下

主页配置分为五个部分: 自动回复, 浏览首页, 下载指定账户数据, 评论指定用户作品, 以及从指定用户的评论区私聊别人(小红书不支持).

- operate: 配置自动回复, 抖音可以自动回复私聊. 回复内容由"common"配置决定
- explore(小红书)/discover(抖音): 配置浏览主页的内容
  - 包括浏览数量及浏览时是否需要点赞收藏
  - @某人时小红书建议填写小红书名, 抖音建议填写抖音号
  - 如果配置了AI, 可以在浏览时过滤内容: 不喜欢的作品不会点赞, 收藏和评论
- download: 下载指定用户的数据, 只会下载用户主页可见的数据, 不会下载对应评论
- comment: 评论指定用户的作品, 如果配置了AI可以个性化评论
- follow: 从视频评论区选择用户发送私信, 私信内容是"default_chat_message". 默认按顺序选择, 如果配置了AI则可以通过用户评论选择性私聊

## 写在最后

配置多个账户时注意事项
 
- 不同平台, 同一平台的主页和创作者中心页可以同时启动
- 配置中同一个"account"最多同时打开【抖音主页, 抖音创作者中心, 小红书主页, 小红书创作者中心】4个界面
- 同一个平台多账户需要配置中填写不同的"account"名称
- 电脑性能决定同时启动账户的数量, 建议不要在同一个ip地址登录多个账户
