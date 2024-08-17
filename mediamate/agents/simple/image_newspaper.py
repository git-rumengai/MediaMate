"""
This module contains the ImageNewspaper class which is responsible for fetching news from Google News,
converting it to Markdown format, and saving it as images to various platforms.
"""
import os
from datetime import datetime, timedelta
from typing import Tuple, List


from mediamate.tools.duckduckgo import AsyncDDGS
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
        self.cti = ConvertToImage()
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
        self.md_news = []

    def init(self, title: str = '', keywords: Tuple[str, ...] = (), topic: str = ''):
        """
        topic： google_news需要
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
                   wait_minute: int = 3,
                   theme: str = '',
                   download: str = '否'
                   ):
        """
        Initialize media configuration.
        """
        self.media_config['title'] = title or self.media_config['title']
        self.media_config['desc'] = describe or self.media_config['desc']
        self.media_config['labels'] = list(labels) or self.media_config['labels']
        self.media_config['location'] = location or self.media_config['location']
        self.media_config['wait_minute'] = wait_minute or self.media_config['wait_minute']
        self.media_config['theme'] = theme or self.media_config['theme']
        self.media_config['download'] = download or self.media_config['download']
        return self

    def set_params(self, topic: str, query: str, limit: int = 5):
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
            max_results=limit
        )

    async def get_ddgs_news(self, limit: int = 5, days: int = 7) -> List[str]:
        """ timelimit设置为None, 然后自己对新闻排序并过滤 """
        self.md_news = []
        for query in self.news_config['keywords']:
            news = await AsyncDDGS().anews(query, region='cn-zh', safesearch='off', timelimit=None, max_results=limit)
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
                    md_text = f"""# {self.news_config['title']}: {query}\n """
                    for inner, item in enumerate(recent_news):
                        md_text += f"""\n#### {item['title'].strip()}\n\n> 详情:{item['body'].strip()}\n\n发布日期:{item['date'].strip()} """
                    self.md_news.append(md_text)
        return self.md_news

    async def get_google_news(self, limit: int = 5, days: int = 7) -> List[str]:
        """
        Fetch news from Google News and convert it to Markdown format.

        :return: A list of Markdown formatted news.
        """
        self.md_news = []
        for query in self.news_config['keywords']:
            self.set_params(self.news_config['topic'], query, limit=limit)
            news = self.google_news.export_news()
            # 过滤并排序
            if news:
                recent_news = sorted(
                    (item for item in news
                     if
                     datetime.strptime(item['publish_date'], '%a, %d %b %Y %H:%M:%S %Z') >= datetime.now() - timedelta(days=days)),
                    key=lambda x: datetime.strptime(x['publish_date'], '%a, %d %b %Y %H:%M:%S %Z'),
                    reverse=True
                )
                if recent_news:
                    md_text = f"""# {self.news_config['title']}: {query}\n """
                    for inner, item in enumerate(recent_news):
                        md_text += f"""\n### {inner + 1}. **{item['title']}**\n- 来源:{item['source']} \n- 发布日期:{item['publish_date']} """
                    self.md_news.append(md_text)
        return self.md_news

    async def save_to_xhs(self):
        """
        Save the fetched news to the XHS platform as images.
        """
        media_config = config.MEDIA.get('media')
        if media_config:
            for xhs in media_config.get('xhs', []):
                account = xhs['account']
                platform = xhs['platform']
                account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/image_news'
                os.makedirs(account_dir, exist_ok=True)
                for index, news in enumerate(self.md_news):
                    print(news)
                    print(f'{account_dir}/{index}.png')
                    await self.cti.markdown_to_image(news, f'{account_dir}/{index}.png')
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
        media_config = config.MEDIA.get('media')
        if media_config:
            for dy in media_config.get('dy', []):
                account = dy['account']
                platform = dy['platform']
                account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/image_news'
                os.makedirs(account_dir, exist_ok=True)
                for index, news in enumerate(self.md_news):
                    await self.cti.markdown_to_image(news, f'{account_dir}/{index+1}.png')
                self.metadata.init(f'{account_dir}/metadata.yaml')
                await self.metadata.set('标题', self.media_config['title'])
                await self.metadata.set('描述', self.media_config['desc'])
                await self.metadata.set('标签', self.media_config['labels'])
                await self.metadata.set('地点', self.media_config['location'])
                await self.metadata.set('贴纸', self.media_config['theme'])
                await self.metadata.set('视频超时报错', self.media_config['wait_minute'])
                await self.metadata.set('允许保存', self.media_config['download'])
                logger.info(f'数据已保存至: {account_dir}')
