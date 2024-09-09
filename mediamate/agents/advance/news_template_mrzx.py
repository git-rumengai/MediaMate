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


class NewsTemplateMrzx:
    def __init__(self):
        self.convert = ConvertToImage()
        self.web_news = WebNews()

    async def get_html(self,
                       title: dict,
                       qr_code: str,
                       news_keywords: dict,
                       data_imag: str,
                       blacklist: Tuple[str, ...] = (),
                       limit: int = 5,
                       days: int = 7,
                       truncat:bool = True,
                       sentence: int = 2
                       ) -> str:
        """
        异步生成HTML页面。

        该函数根据提供的新闻关键词从网络上获取新闻，并结合其它参数生成一个HTML页面。

        参数:
            - title: 海报的标题信息。
            - qr_code: 字符串，表示二维码图片的路径或URL。
            - news_keywords: 字典，关键词及其对应的新闻类别，用于从网络上检索新闻。
            - data_imag: 字符串，指定的数据图片路径或URL。
            - blacklist: 包含一组黑名单中的关键词，用于过滤新闻标题和内容。
            - limit: 整数，限制返回的新闻数量。
            - days: 整数，规定天数内获取的新闻。
            - truncat: 布尔值，决定是否截断新闻内容。
            - sentence: 整数，指定截断的句子数。

        返回:
            - str: 生成的HTML页面内容。
        """
        template_data = {}
        template_data['date'] = datetime.today().strftime('%Y/%m/%d')
        template_data.update(title)
        template_data['qr_code'] = qr_code
        all_news = {}
        for key, value in news_keywords.items():
            news = await self.web_news.get_ddgs_news(value, blacklist=blacklist, limit=limit, days=days, truncat=truncat, sentence=sentence)
            news_content1 = []
            for inner in news:
                news_content1.append({'title': inner['title'], 'content': inner['body']})
            all_news[key] = news_content1
        template_data['all_news'] = all_news
        template_data['data_imag'] = data_imag
        # 设置模板环境
        env = Environment(loader=FileSystemLoader(f'{config.PROJECT_DIR}/static/html'))
        template = env.get_template('news_mrzx.html')
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
            news_mrzx_path = os.path.join(media_path.upload, 'news_zhdl')
            if os.path.exists(news_mrzx_path):
                shutil.rmtree(news_mrzx_path)
            os.makedirs(news_mrzx_path, exist_ok=True)

            await self.save_html_content(html_content, news_mrzx_path)
            metadata_config = ConfigManager(f'{news_mrzx_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('地点', metadata.get('地点'))
            logger.info(f'数据已保存至: {news_mrzx_path}')

    async def save_to_dy(self, html_content, metadata: dict):
        """ 保存到抖音上传目录 """
        media_config = config.MEDIA.get('media', {})
        dy_config = media_config.get('dy', [])
        for dy in dy_config:
            media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
            media_path = MediaPath(info=media_info)
            news_mrzx_path = os.path.join(media_path.upload, 'news_zhdl')
            if os.path.exists(news_mrzx_path):
                shutil.rmtree(news_mrzx_path)
            os.makedirs(news_mrzx_path, exist_ok=True)

            await self.save_html_content(html_content, news_mrzx_path)
            metadata_config = ConfigManager(f'{news_mrzx_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('音乐', metadata.get('音乐'))
            await metadata_config.set('地点', metadata.get('地点'))
            await metadata_config.set('贴纸', metadata.get('贴纸'))
            await metadata_config.set('允许保存', metadata.get('允许保存'))
            logger.info(f'数据已保存至: {news_mrzx_path}')
