from playwright.async_api import Page

from mediamate.utils.log_manager import log_manager
from mediamate.platforms.xhs.homepage import XhsHomepage

logger = log_manager.get_logger(__file__)


class XhsOperator(XhsHomepage):
    """ 小红书网页无法私聊 """

    async def click_comment(self, page: Page) -> Page:
        """
        进入个人页回复评论
        1. 过滤仅自己可见图文
        2. 过滤日期超过days天的图文
        3.
        """
        logger.info('进入个人页')
        steps = ('me', )
        await self.ensure_step_page(page, steps)

        no_section = await self.get_locator(page, 'section no_section')
        section_list = await self.get_locator(page, 'section section_list')
        section_index = await self.wait_first_locator([no_section, section_list.first])
        if section_index == 0:
            logger.info('没有笔记, 跳过')
            return page

        section_list = await section_list.all()
        for section in section_list[:self.default_reply_comment_times]:
            onlyme = await self.get_child_locator(section, 'section section_list _onlyme')
            if await onlyme.is_visible():
                logger.info('仅自己可见')
                continue

            await self.ensure_close(page)
            logger.info('点击封面')
            img = await self.get_child_locator(section, 'section section_list _img')
            await img.click()
            await self.handle_comment_reply(page)
        return page


__all__ = ['XhsOperator']
