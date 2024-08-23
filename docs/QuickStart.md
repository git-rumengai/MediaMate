# 快速上手项目

## 首次运行
1. 新建.env文件内容如下:
```yaml
MM__DATA=data   # 数据目录名, 项目同级目录下
```
2. 新建.media.yaml文件内容如下, xhs/dy配置任选:
```yaml
# 个人信息
media:
  xhs:
    - platform: 'xiaohongshu'             # 固定
      account: 'RuMengAI'                 # 数据保存文件夹名, 任意取
      headless: False                     # 无头模式启动浏览器, False会打开浏览器界面

      home:                                   # 配置: 小红书官网页
        explore:                             # 配置: 浏览小红书发现页, 通过"ai_prompt_content_filter"可以过滤视频内容
          topics: ['美食', '旅行']     # 浏览的主题
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

      home:                                     # 配置: 抖音官网首页
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
```
3. 执行如下代码(小红书: /examples/ex_dy.py, 抖音: /examples/ex_dy.py)
> 确保当前网络状况正常, 网速正常. 首次执行需要手动登录账户 
```python
import asyncio
from mediamate.platforms.dy.client import DyClient
from mediamate.config import config
from mediamate.utils.schemas import MediaInfo
from mediamate.utils.enums import UrlType


async def run_dy():
    """  """
    media_config = config.MEDIA.get('media')
    if media_config:
        dy_config = media_config.get('dy', [])
        for i in dy_config:
            tasks = []
            if i.get('home'):
                home_client = DyClient(MediaInfo(url=UrlType.DY_HOME_URL, **i))
                tasks.append(home_client.start_home())
            if i.get('creator'):
                creator_client = DyClient(MediaInfo(url=UrlType.DY_CREATOR_URL, **i))
                tasks.append(creator_client.start_creator())
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(run_dy())
```
4. 确保网络通畅. 如果顺利, 你应该可以看到每一步操作的详细步骤

## 自动发表内容

> 请注意: 程序会自动发表内容, 首次执行需要手动登录账户 

1. 重新在".env"文件中添加如下配置:
```yaml
# 个人信息
media:
  xhs:
    - platform: 'xiaohongshu'             # 固定
      account: 'RuMengAI'                 # 数据保存文件夹名, 任意取
      headless: False                     # 无头模式启动浏览器, False会打开浏览器界面
      
      creator:                               # 配置: 小红书创作者中心
        upload: True                         # 是否自动上传视频/图文
  dy:
    - platform: 'douyin'        # 固定
      account: 'RuMengAI'       # 数据保存文件夹名, 任意取
      headless: False           # 无头模式启动浏览器, False会打开浏览器界面

      creator:                      # 配置: 抖音创作者中心
        upload: True                # 是否自动上传视频/图文
```
2. 运行"/examples/ex_demo.py"获取一个demo文件(可以检查自己的"/data/upload"文件夹内容)
3. 运行程序启动程序【**注意: 会自动发表**】(小红书: /examples/ex_dy.py, 抖音: /examples/ex_dy.py)
4. 程序会将"/data/upload/douyin/RuMengAI/"目录下所有文件夹的内容都自动上传

## 使用代理

在".env"和".media.yaml"文件中都可以配置代理
".env"
```yaml
# 固定代理
# MM__FIXED_PROXY=http://.../

# 从代理池中选择的代理会频繁更换
MM__PROXY_NAME=KDL
MM__PROXY_BACKUP=3
# 快代理的私密代理
MM__KDL_USERNAME=
MM__KDL_PASSWORD=
MM__KDL_SECRETID=
MM__KDL_SECRETKEY=
```
".media.yaml"
```yaml
media:
  xhs:
    - platform: 'xiaohongshu'             # 固定
      account: 'RuMengAI'                 # 数据保存文件夹名, 任意取
      headless: False                     # 无头模式启动浏览器, False会打开浏览器界面
      proxy: 'http://.../'                
```
区别在于".env"配置的是全局代理,  ".media.yaml"可以为每一个账户单独使用一个代理. 如果所有代理同时配置, 使用优先级为:
> 账户代理 > 固定代理 > 代理池代理

> 注意事项: 账户使用代理后会将代理数据保存到"/data/active/douyin/RuMengAI/_config.yaml"文件中, 如果下次使用想禁用代理, 在账户配置中设置
```yaml
media:
  xhs:
    - platform: 'xiaohongshu'             # 固定
      account: 'RuMengAI'                 # 数据保存文件夹名, 任意取
      headless: False                     # 无头模式启动浏览器, False会打开浏览器界面
      proxy: 'close'                      # 使用代理后会被默认保存, 填写close关闭代理
```

## 使用AI功能
1. 进入 [302.AI](https://gpt302.saaslink.net/t2ohlA) (链接有优惠)官网注册并申请APIKEY.
2. 将配置填写到".env"文件中
```yaml
# 302AI
MM__302__APIKEY=sk-...
MM__302__LLM=gpt-4o-mini
```
3. 运行如下任意程序可以看到对应的"/data/upload"目录下已经生成了完整的可发表内容
- "/examples/ex_logo.py"
- "/examples/ex_news.py"
- "/examples/ex_photo.py"
- "/examples/ex_media.py"

> 这三个程序只是简单写的demo, 希望你能向我们提交更多想法和创意

# 总结

到目前为止, 你应该对我们项目的功能有大致的了解. 我们已经尽量确保程序能够流畅运行, 但是使用playwright完全模拟人类的操作确实还有很多困难, 请确保程序运行过程中网络流畅.
如果遇到问题或者有什么新的想法, 可以及时向我们反馈.
