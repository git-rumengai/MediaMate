import os
import shutil
from datetime import datetime, timedelta
from typing import Tuple, List

from mediamate.tools.duckduckgo import AsyncDDGS
from mediamate.tools.convert.convert_to_image import ConvertToImage
from mediamate.config import config, ConfigManager
from mediamate.utils.log_manager import log_manager
from mediamate.utils.schema import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType


logger = log_manager.get_logger(__file__)


class ImageNewspaper:
    """ 从Google获取新闻, 转Markdown, 再转图片 """
    def __init__(self, title: str, keywords: Tuple[str, ...]):
        self.cti = ConvertToImage()
        self.md_news = []
        self.title = title
        self.keywords = keywords

    async def get_ddgs_news(self, limit: int, days: int) -> List[str]:
        """ 获取新闻 """
        self.md_news = []
        for keyword in self.keywords:
            news = await AsyncDDGS().anews(keyword, region='cn-zh', safesearch='off', timelimit=None, max_results=limit)
            # 过滤并排序
            if news:
                recent_news = sorted(
                    (item for item in news
                     if
                     datetime.fromisoformat(item['date']).replace(tzinfo=None) >= datetime.now() - timedelta(days=days)),
                    key=lambda x: datetime.fromisoformat(x['date']).replace(tzinfo=None),
                    reverse=True
                )
                if recent_news:
                    md_text = f"""# {self.title}: {keyword}\n """
                    for inner, item in enumerate(recent_news):
                        md_text += f"""\n#### {item['title'].strip()}\n\n> 详情:{item['body'].strip()}\n\n发布日期:{item['date'].strip()} """
                    self.md_news.append(md_text)
        return self.md_news

    async def save_to_xhs(self, metadata: dict, limit: int = 5, days: int = 7):
        """ 保存到小红书上传目录 """
        if len(self.md_news) == 0:
            await self.get_ddgs_news(limit, days)
        media_config = config.MEDIA.get('media', {})
        xhs_config = media_config.get('xhs', [])
        for xhs in xhs_config:
            media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
            media_path = MediaPath(info=media_info)
            image_news_path = os.path.join(media_path.upload, 'image_news')
            if os.path.exists(image_news_path):
                shutil.rmtree(image_news_path)
            os.makedirs(image_news_path, exist_ok=True)
            for index, news in enumerate(self.md_news):
                await self.cti.markdown_to_image(news, f'{image_news_path}/{index}.png')
            metadata_config = ConfigManager(f'{image_news_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('地点', metadata.get('地点'))
            logger.info(f'数据已保存至: {image_news_path}')

    async def save_to_dy(self, metadata: dict, limit: int = 5, days: int = 7):
        """ 保存到抖音上传目录 """
        if len(self.md_news) == 0:
            await self.get_ddgs_news(limit, days)
        media_config = config.MEDIA.get('media', {})
        dy_config = media_config.get('dy', [])
        for dy in dy_config:
            media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
            media_path = MediaPath(info=media_info)
            image_news_path = os.path.join(media_path.upload, 'image_news')
            if os.path.exists(image_news_path):
                shutil.rmtree(image_news_path)
            os.makedirs(image_news_path, exist_ok=True)
            for index, news in enumerate(self.md_news):
                await self.cti.markdown_to_image(news, f'{image_news_path}/{index}.png')
            metadata_config = ConfigManager(f'{image_news_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('音乐', metadata.get('音乐'))
            await metadata_config.set('地点', metadata.get('地点'))
            await metadata_config.set('贴纸', metadata.get('贴纸'))
            await metadata_config.set('允许保存', metadata.get('允许保存'))
            logger.info(f'数据已保存至: {image_news_path}')
