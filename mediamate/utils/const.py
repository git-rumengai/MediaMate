""" Constant configuration module """
# redis数据库(未启用)
REDIS_PROXY_DB = 1

HTTP_BIN = 'https://httpbin.org/ip'
TRACE_PLAYWRIGHT_DEV = 'https://trace.playwright.dev/'
DEFAULT_URL_TIMEOUT = 60 * 1000                 # 打开网页的默认等待时间: min
DEFAULT_LOCATION = (121.467863, 31.167847)      # 默认地址, 上海



# 这些会被参数覆盖掉
DEFAULT_COMMENT = '谢谢分享！ '
DEFAULT_REPLY_COMMENT = '谢谢评论！ '
DEFAULT_CHAT = '你好, 🤝'
DEFAULT_REPLY_CHAT = '你好👐'

DEFAULT_VIDEO_WAIT = 15                         # 默认上传视频最长等待时间
DEFAULT_IMAGE_WAIT = 3                          # 默认上传图片最长等待时间

DEFAULT_DATA_LENGTH = 10                        # 默认获取数据长度: 10条
DEFAULT_REPLY_CHAT_LENGTH = 10                  # 默认回复私聊数量: 10条
DEFAULT_REPLY_COMMENT_LENGTH = 10               # 默认回复评论数量: 10条
DEFAULT_REPLY_COMMENT_DAYS = 7                  # 默认回复最近7天的图文
DEFAULT_REPLY_COMMENT_TIMES = 5                 # 默认回复最近5篇图文

