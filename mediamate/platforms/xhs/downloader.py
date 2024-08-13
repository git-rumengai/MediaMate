import os
import json
from typing import Optional, Tuple
from playwright.async_api import Page

from mediamate.utils.schemas import MediaLoginInfo
from mediamate.utils.log_manager import log_manager
from mediamate.config import config
from mediamate.platforms.base import BaseLocator

logger = log_manager.get_logger(__file__)


class XhsDownloader(BaseLocator):
    """ 下载数据 """
    def __init__(self):
        super().__init__()
        self.download_data_dir = ''
        self.download_user_dir = ''

    def init(self, info: MediaLoginInfo):
        """  """
        elements_path = f'{config.PROJECT_DIR}/platforms/static/elements/xhs/creator.yaml'
        super().init(elements_path)

        self.download_data_dir = f'{config.DATA_DIR}/download/xiaohongshu/{info.account}'
        self.download_user_dir = f'{self.download_data_dir}/user_data'
        os.makedirs(self.download_user_dir, exist_ok=True)
        return self

    async def ensure_page(self, page: Page) -> Page:
        """ """
        return page

    async def click_inspiration(self, page: Page, topics: Tuple[str, ...] = ()) -> Optional[Page]:
        """  """
        steps = ('inspiration', )
        await self.ensure_step_page(page, steps)
        topic_list = await self.get_visible_locators(page, 'inspiration topic_list')
        topic_list = await topic_list.all()
        content_list = await self.get_visible_locators(page, 'inspiration content_list')

        topics = topics or ('美食, ')
        result = {}
        for topic in topic_list:
            topic_text = await topic.inner_text()
            if not topic_text.strip() in topics:
                continue
            await topic.click()
            contents = await content_list.all()
            result[topic_text] = []
            for content in contents:
                url = await self.get_child_visible_locator(content, 'inspiration content_list _url')
                url_text = await url.get_attribute('href')
                title = await self.get_child_visible_locator(content, 'inspiration content_list _title')
                title_text = await title.inner_text()
                view = await self.get_child_visible_locator(content, 'inspiration content_list _view')
                view_text = await view.inner_text()
                logger.info(f'主题: {title_text}, 观看数: {view_text}')
                result[topic_text].append({
                    'url': url_text,
                    'title': title_text.strip(),
                    'view': view_text.strip()
                })
        with open(f'{self.download_user_dir}/content_inspiration.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        # 保存数据
        return page


__all__ = ['XhsDownloader']
