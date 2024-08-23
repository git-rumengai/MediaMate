import json
from typing import Optional, Tuple
from playwright.async_api import Page

from mediamate.utils.log_manager import log_manager
from mediamate.platforms.base import BaseLocator

logger = log_manager.get_logger(__file__)


class XhsDownloader(BaseLocator):
    """ 下载数据 """
    async def ensure_page(self, page: Page) -> Page:
        """ """
        return page

    async def click_inspiration(self, page: Page, topics: Tuple[str, ...] = ()) -> Optional[Page]:
        """ 点击灵感笔记 """
        logger.info('下载笔记灵感数据')
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
                    '地址': url_text,
                    '标题': title_text.strip(),
                    '浏览数': view_text.strip()
                })
        with open(f'{self.data_path.download_personal}/笔记灵感.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            logger.info('笔记灵感数据下载完毕')
        # 保存数据
        return page

    async def click_creator(self, page: Page) -> Optional[Page]:
        """ 数据中心: 首页数据 """
        logger.info('下载总览数据')
        steps = ('datacenter', 'datacenter summary_text')
        await self.ensure_step_page(page, steps)
        data_list = await self.get_visible_locators(page, 'datacenter data_list')
        data_all = await data_list.all_inner_texts()
        data_all_text = [i.strip() for i in data_all]
        data = {
            '新增粉丝': data_all_text[0],
            '主页访客': data_all_text[1],
            '观看数': data_all_text[2],
            '互动数': data_all_text[3],
        }

        with open(f'{self.data_path.download_personal}/数据总览.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info('总览数据已保存')
        # 保存数据
        return page


__all__ = ['XhsDownloader']
