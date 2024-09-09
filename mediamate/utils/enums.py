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
    LOGIN = 'login'
    DOWNLOAD = 'download'
    UPLOAD = 'upload'
    COMMENT = 'comment'
    REPLY = 'reply'


class Resolution(Enum):
    HD = (1280, 720)         # 720p
    FULL_HD = (1920, 1080)   # 1080p
    QHD = (2560, 1440)       # 1440p
    ULTRA_HD = (3840, 2160)  # 4K


class VideoOrientation(Enum):
    LANDSCAPE = (16, 9)   # 横屏，16:9
    PORTRAIT = (9, 16)    # 竖屏，9:16


class FPS(Enum):
    FPS_3 = 3
    FPS_24 = 24
    FPS_30 = 30
    FPS_60 = 60


class TophubType(Enum):
    TECH = "科技"
    ENT = "娱乐"
    COM = "社区"
    SHOP = "购物"
    FIN = "财经"
    DEV = "开发"
    DES = "设计"
    PNM = "报刊"

