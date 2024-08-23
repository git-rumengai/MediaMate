"""
This module defines data models (schemas) used for data validation and serialization.

"""
import os
from pydantic import BaseModel, constr
from typing import Tuple, Optional
from datetime import datetime

from mediamate.config import config
from mediamate.utils.enums import UrlType, MediaActionType
from urllib.parse import urlparse


class MediaInfo(BaseModel):
    url: UrlType
    # 账户参数
    account: constr(min_length=1) = ''
    headless: bool = True
    proxy: str = ''
    common: dict = {}
    home: dict = {}
    creator: dict = {}

    domain: str = ''
    subdomain: str = ''

    def __init__(self, **data):
        super().__init__(**data)
        self.subdomain, self.domain = self._extract_domain(self.url)

    @staticmethod
    def _extract_domain(url: UrlType) -> Tuple[str, str]:
        """ 解析域名 """
        parsed_url = urlparse(url.value)
        domain_parts = parsed_url.netloc.split('.')

        if len(domain_parts) == 3:
            subdomain = domain_parts[0]
            domain = domain_parts[1]
        elif len(domain_parts) == 2:
            subdomain = ''
            domain = domain_parts[0]
        else:
            raise ValueError(f'域名解析错误: {url.value}')
        return subdomain, domain


class MediaPath(BaseModel):
    info: MediaInfo
    logs: Optional[str] = None
    logs_file: Optional[str] = None

    upload: Optional[str] = None
    download: Optional[str] = None
    download_personal: Optional[str] = None
    download_personal_chat_file: Optional[str] = None
    download_public: Optional[str] = None

    browser: Optional[str] = None
    browser_home: Optional[str] = None
    browser_creator: Optional[str] = None

    active: Optional[str] = None
    active_config_file: Optional[str] = None

    elements: Optional[str] = None
    elements_common_file: Optional[str] = None
    elements_home_file: Optional[str] = None
    elements_creator_file: Optional[str] = None

    static_imgs: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        """ 自动填充默认路径 """
        # 日志路径
        self.logs = os.path.join(config.DATA_DIR, 'logs')
        os.makedirs(self.logs, exist_ok=True)

        self.logs_file = os.path.join(self.logs, 'MediaMate.log')
        # 上传数据保存目录
        self.upload = os.path.join(config.DATA_DIR, f'upload/{self.info.domain}/{self.info.account}')
        os.makedirs(self.upload, exist_ok=True)

        # 下载数据保存目录
        self.download = os.path.join(config.DATA_DIR, f'download/{self.info.domain}/{self.info.account}')
        self.download_personal = os.path.join(self.download, 'personal')
        os.makedirs(self.download_personal, exist_ok=True)
        self.download_personal_chat_file = os.path.join(self.download_personal, 'personal_chat.yaml')
        self.download_public = os.path.join(self.download, 'public')
        os.makedirs(self.download_public, exist_ok=True)

        # 浏览器数据保存目录
        self.browser = os.path.join(config.DATA_DIR, f'browser/{self.info.domain}/{self.info.account}')
        self.browser_home = os.path.join(self.browser, 'home')
        os.makedirs(self.browser_home, exist_ok=True)
        self.browser_creator = os.path.join(self.browser, 'creator')
        os.makedirs(self.browser_creator, exist_ok=True)
        # 程序运行中经常变动的文件
        self.active = os.path.join(config.DATA_DIR, f'active/{self.info.domain}/{self.info.account}')
        os.makedirs(self.active, exist_ok=True)
        self.active_config_file = os.path.join(self.active, '_config.yaml')
        # 定位节点存放目录
        self.elements = os.path.join(config.PROJECT_DIR, 'platforms/static/elements')
        os.makedirs(self.elements, exist_ok=True)
        self.elements_common_file = os.path.join(self.elements, 'common.yaml')
        self.elements_home_file = os.path.join(self.elements, f'{self.info.domain}/home.yaml')
        self.elements_creator_file = os.path.join(self.elements, f'{self.info.domain}/creator.yaml')
        # 静态图片目录
        self.static_imgs = os.path.join(config.PROJECT_DIR, 'platforms/static/imgs')
        os.makedirs(self.static_imgs, exist_ok=True)


class MediaActionRecord(BaseModel):
    """  """
    action: MediaActionType
    start_time: datetime
    end_time: datetime

    record_time: str = None
    duration: int = None

    # 在初始化时计算 record_time 和 duration
    def __init__(self, **data):
        super().__init__(**data)
        self.record_time = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.duration = int((self.end_time - self.start_time).total_seconds())

    # 输出字符串格式的方法
    def to_string(self) -> str:
        return f"action: {self.action}, record_time: {self.record_time}, duration: {self.duration}s"
