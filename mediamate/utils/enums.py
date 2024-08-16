from enum import Enum


class PlatformType(Enum):
    DY = 'douyin'
    XHS = 'xiaohongshu'


class LocatorType(Enum):
    HOME = 'home'
    CREATOR = 'creator'


class VerifyType(Enum):
    MOVE = 'move'
    ROTATE = 'rotate'


class MediaType(Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    IMAGE = 'image'
    TEXT = 'text'
    UNKNOW = 'unknow'
