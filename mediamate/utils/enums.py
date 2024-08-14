from enum import Enum


class PlatformType(Enum):
    DY = 'douyin'
    XHS = 'xiaohongshu'


class LocatorType(Enum):
    HOME = 'home'
    CREATOR = 'creator'


class MediaType(Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    IMAGE = 'image'
    TEXT = 'text'
    UNKNOW = 'unknow'
