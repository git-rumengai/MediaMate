from typing import Optional
from playwright.async_api import Page
from mediamate.utils.log_manager import log_manager
from mediamate.platforms.dy.homepage import DyHomepage


logger = log_manager.get_logger(__file__)


class DyOperator(DyHomepage):
    """ 回复评论及私聊 """

    async def click_comment(self, page: Page) -> Optional[Page]:
        """ 进入个人页回复评论, 通过主页评论 """
        logger.info('处理评论')
        me = await self.get_visible_locator(page, 'me')
        await me.hover()
        await me.click()
        no_section = await self.get_locator(page, 'section no_section')
        section_list = await self.get_locator(page, 'section section_list')
        section_index = await self.wait_first_locator([no_section, section_list.first])
        if section_index == 0:
            logger.info('没有作品, 忽略')
            return page
        section_list = await section_list.all()
        for section in section_list[:self.default_reply_comment_times]:
            await self.ensure_player_close(page)
            logger.info('点击封面')
            img = await self.get_child_locator(section, 'section section_list _img')
            await img.click()
            await self.handle_comment_reply(page)
        return page

    async def click_chat(self, page: Page) -> Optional[Page]:
        """ 通过主页处理私信 """
        logger.info('处理私信')
        count = 0
        while True:
            count += 1
            page = await self.enter_chat(page)
            if count > self.default_reply_chat_length:
                break
        return page


__all__ = ['DyOperator']
