from enum import Enum


class UrlType(Enum):
    XHS_HOME_URL = 'https://www.xiaohongshu.com'
    XHS_CREATOR_URL = 'https://creator.xiaohongshu.com/creator/home'
    DY_HOME_URL = 'https://www.douyin.com'
    DY_CREATOR_URL = 'https://creator.douyin.com/creator-micro/home'


class VerifyType(Enum):
    MOVE = 'move'
    ROTATE = 'rotate'


class MediaType(Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    IMAGE = 'image'
    TEXT = 'text'
    UNKNOW = 'unknow'


class MediaActionType(Enum):
    UPLOAD = '上传'
    BROWSE = '浏览'
    COMMENT = '评论'
    CHAT = '私聊'
    ERROR = '未知错误'
