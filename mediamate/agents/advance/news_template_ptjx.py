import os
import shutil
from typing import Tuple
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from mediamate.tools.duckduckgo.web_news import WebNews
from mediamate.tools.convert.convert_to_image import ConvertToImage
from mediamate.config import config, ConfigManager
from mediamate.utils.log_manager import log_manager
from mediamate.utils.schema import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType


logger = log_manager.get_logger(__file__)


class NewsTemplatePtjx:
    def __init__(self):
        self.convert = ConvertToImage()
        self.web_news = WebNews()

    async def get_html(self,
                       title: str,
                       qr_code: str,
                       keywords: list,
                       blacklist: Tuple[str, ...] = (),
                       limit: int = 5,
                       days: int = 7
                       ) -> str:
        """  """
        template_data = {}
        template_data['title'] = title
        template_data['date'] = datetime.today().date().strftime('%Y年%m月%d日')
        template_data['qr_code'] = qr_code
        news = await self.web_news.get_ddgs_news(keywords, blacklist=blacklist, limit=limit, days=days, force_image=True)
        for index, new in enumerate(news):
            news[index]['date'] = datetime.fromisoformat(new['date']).strftime('%Y-%m-%d %H:%M')
        template_data['news_list'] = news
        # 设置模板环境
        env = Environment(loader=FileSystemLoader(f'{config.PROJECT_DIR}/static/html'))
        template = env.get_template('news_ptjx.html')
        rendered_html = template.render(template_data)
        return rendered_html

    async def save_html_content(self, html_content: str, save_dir: str):
        """  """
        await self.convert.html_to_image(html_content, f'{save_dir}/0.png', use_phone=True)
        # 将渲染后的内容保存到文件
        with open(f'{save_dir}/0.html', 'w', encoding='utf-8') as file:
            file.write(html_content)

    async def save_to_xhs(self, html_content: str, metadata: dict):
        """ 保存到小红书上传目录 """
        media_config = config.MEDIA.get('media', {})
        xhs_config = media_config.get('xhs', [])
        for xhs in xhs_config:
            media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
            media_path = MediaPath(info=media_info)
            news_ptjx_path = os.path.join(media_path.upload, 'news_ptjx')
            if os.path.exists(news_ptjx_path):
                shutil.rmtree(news_ptjx_path)
            os.makedirs(news_ptjx_path, exist_ok=True)

            await self.save_html_content(html_content, news_ptjx_path)
            metadata_config = ConfigManager(f'{news_ptjx_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('地点', metadata.get('地点'))
            logger.info(f'数据已保存至: {news_ptjx_path}')

    async def save_to_dy(self, html_content, metadata: dict):
        """ 保存到抖音上传目录 """
        media_config = config.MEDIA.get('media', {})
        dy_config = media_config.get('dy', [])
        for dy in dy_config:
            media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
            media_path = MediaPath(info=media_info)
            news_ptjx_path = os.path.join(media_path.upload, 'news_ptjx')
            if os.path.exists(news_ptjx_path):
                shutil.rmtree(news_ptjx_path)
            os.makedirs(news_ptjx_path, exist_ok=True)

            await self.save_html_content(html_content, news_ptjx_path)
            metadata_config = ConfigManager(f'{news_ptjx_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('音乐', metadata.get('音乐'))
            await metadata_config.set('地点', metadata.get('地点'))
            await metadata_config.set('贴纸', metadata.get('贴纸'))
            await metadata_config.set('允许保存', metadata.get('允许保存'))
            logger.info(f'数据已保存至: {news_ptjx_path}')
