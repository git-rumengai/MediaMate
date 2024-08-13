"""
This module contains the ImageNewspaper class which is responsible for fetching news from Google News,
converting it to Markdown format, and saving it as images to various platforms.
"""
import os
from typing import Tuple, List
from mediamate.tools.google_news.client import GoogleNewsClient
from mediamate.tools.converter.convert_to_image import ConvertToImage
from mediamate.config import config, ConfigManager
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class ImageNewspaper:
    """
    The ImageNewspaper class handles fetching news from Google News, converting it to Markdown format,
    and saving it as images to various platforms.
    """
    def __init__(self):
        self.google_news = GoogleNewsClient()
        self.tti = ConvertToImage()
        self.metadata = ConfigManager()

        self.news_config = {
            'title': '科技新闻报',
            'topic': 'Technology',
            'keywords': ['微软', '谷歌', '苹果公司', '英伟达', '腾讯', '字节跳动', '阿里巴巴']
        }

        self.media_config = {
            'title': '新闻导读',
            'desc': '科技新闻报道',
            'labels': ['RuMengAI', '新闻', '科技'],
            'location': '上海',
            'theme': '',
            'wait_minute': 3,
            'download': '否'
        }

    def init(self, title: str = '', topic: str = '', keywords: Tuple[str, ...] = ()):
        """
        Initialize news configuration.
        """
        self.news_config['title'] = title or self.news_config['title']
        self.news_config['topic'] = topic or self.news_config['topic']
        self.news_config['keywords'] = list(keywords) or self.news_config['keywords']
        return self

    def init_media(self,
                   title: str = '',
                   describe: str = '',
                   labels: Tuple[str, ...] = (),
                   location: str = '',
                   theme: str = '',
                   wait_minute: int = 3,
                   download: str = '否'
                   ):
        """
        Initialize media configuration.
        """
        self.media_config['title'] = title or self.media_config['title']
        self.media_config['desc'] = describe or self.media_config['desc']
        self.media_config['labels'] = list(labels) or self.media_config['labels']
        self.media_config['location'] = location or self.media_config['location']
        self.media_config['theme'] = theme or self.media_config['theme']
        self.media_config['wait_minute'] = wait_minute or self.media_config['wait_minute']
        self.media_config['download'] = download or self.media_config['download']
        return self

    def set_params(self, topic: str, query: str):
        """
        Set parameters for the Google News client.

        :param topic: The topic of the news.
        :param query: The query to search for.
        """
        self.google_news.set_params(
            location='China',
            language='chinese simplified',
            topic=topic,
            query=query,
            max_results=5
        )

    async def get_md_news(self) -> List[str]:
        """
        Fetch news from Google News and convert it to Markdown format.

        :return: A list of Markdown formatted news.
        """
        md_news = []
        for query in self.news_config['keywords']:
            self.set_params(self.news_config['topic'], query)
            news = self.google_news.export_news()
            if news:
                md_text = f"""### {self.news_config['title']}: {query} """
                for inner, item in enumerate(news):
                    md_text += f"""\n{inner + 1}. **{item['title']}**\n- 来源:{item['source']} \n- 发布日期:{item['publish_date']} """
                md_news.append(md_text)
        return md_news

    async def save_to_xhs(self):
        """
        Save the fetched news to the XHS platform as images.
        """
        md_news = await self.get_md_news()
        media_config = config.MEDIA.get('media')
        if media_config:
            for xhs in media_config.get('xhs', []):
                account = xhs['account']
                platform = xhs['platform']
                account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/image_news'
                os.makedirs(account_dir, exist_ok=True)
                for index, news in enumerate(md_news):
                    await self.tti.markdown_to_image(news, f'{account_dir}/{index}.png')
                self.metadata.init(f'{account_dir}/metadata.yaml')
                await self.metadata.set('标题', self.media_config['title'])
                await self.metadata.set('描述', self.media_config['desc'])
                await self.metadata.set('标签', self.media_config['labels'])
                await self.metadata.set('地点', self.media_config['location'])
                await self.metadata.set('视频超时报错', self.media_config['wait_minute'])
                logger.info(f'数据已保存至: {account_dir}')

    async def save_to_dy(self):
        """
        Save the fetched news to the DY platform as images.
        """
        md_news = await self.get_md_news()
        media_config = config.MEDIA.get('media')
        if media_config:
            for dy in media_config.get('dy', []):
                account = dy['account']
                platform = dy['platform']
                account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/image_news'
                os.makedirs(account_dir, exist_ok=True)
                for index, news in enumerate(md_news):
                    await self.tti.markdown_to_image(news, f'{account_dir}/{index}.png')
                self.metadata.init(f'{account_dir}/metadata.yaml')
                await self.metadata.set('标题', self.media_config['title'])
                await self.metadata.set('描述', self.media_config['desc'])
                await self.metadata.set('标签', self.media_config['labels'])
                await self.metadata.set('地点', self.media_config['location'])
                await self.metadata.set('贴纸', self.media_config['theme'])
                await self.metadata.set('视频超时报错', self.media_config['wait_minute'])
                await self.metadata.set('允许保存', self.media_config['download'])
                logger.info(f'数据已保存至: {account_dir}')
