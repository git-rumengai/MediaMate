import json
import random
from typing import Tuple
from playwright.async_api import Page

from mediamate.utils.log_manager import log_manager
from mediamate.platforms.xhs.homepage import XhsHomepage


logger = log_manager.get_logger(__file__)


class XhsChannel(XhsHomepage):
    """ 主页互动 """

    async def channel_explore(self,
                              page: Page,
                              topics: Tuple[str, ...],
                              times: int = 1,
                              actions: Tuple[str, ...] = (),
                              mention: Tuple[str, ...] = (),
                              ) -> Page:
        """ 随机浏览发现页 """
        logger.info('进入发现页')
        me_name = await self.get_me_name(page)
        if '/explore?' not in page.url:
            steps = ('explore', )
            await self.ensure_step_page(page, steps)
        topic_list = await self.get_visible_locators(page, 'explore topic_list')
        section_list = await self.get_visible_locators(page, 'section section_list')

        topic_list = await topic_list.all()
        for topic in topic_list:
            topic_text = await topic.inner_text()
            if topic_text.strip() not in topics:
                continue
            if topic_text != '推荐':
                await topic.click()
                await self.ensure_page(page)
            logger.info(f'进入主题: {topic_text}')
            sections = await section_list.all()

            times = min(int(times), len(sections))
            for section in sections[:times]:
                await self.ensure_close(page)
                img = await self.get_child_visible_locator(section, 'section section_list _img')
                await img.click()
                page = await self.handle_comment(page, actions, mention, me_name)
                logger.info('关闭窗口')
                await self.wait_medium(page)
                await self.ensure_close(page)
        return page

    async def enter_homepage(self, page: Page, number: str) -> Tuple[Page, bool]:
        """ 通过搜索进入用户主页 """
        # search_url = f'https://www.xiaohongshu.com/search_result?keyword={number}&source=unknown&search_type=user'
        # await page.goto(search_url, timeout=DEFAULT_URL_TIMEOUT)

        search_input = await self.get_visible_locator(page, 'search input')
        await search_input.click()
        await search_input.clear()
        await page.keyboard.type(number)
        input_button = await self.get_visible_locator(page, 'search input_button')
        await self.wait_short(page)
        await input_button.click()
        user = await self.get_visible_locator(page, 'search user')
        await user.click()
        username = await self.get_visible_locator(page, 'search username')
        async with page.expect_popup() as popup_info:
            await username.click()
        new_page = await popup_info.value
        await self.ensure_page(new_page)
        await new_page.wait_for_load_state()
        page = new_page

        return page, True

    async def channel_download(self, page: Page, ids: Tuple[str, ...] = ()) -> Page:
        """ 下载指定用户笔记(不翻页) """
        logger.info('下载指定用户笔记')
        steps = ('explore', )
        await self.ensure_step_page(page, steps)

        for number in ids:
            number = number.strip()
            page, state = await self.enter_homepage(page, number)
            if state:
                user_name = await self.get_visible_locator(page, 'section username')
                user_name_text = await user_name.inner_text()
                user_name_text = user_name_text.strip()

                no_section = await self.get_locator(page, 'section no_section')
                section_list = await self.get_locator(page, 'section section_list')
                await section_list.first.wait_for(state='visible')
                section_index = await self.wait_first_locator([no_section, section_list.first])

                if section_index == 0:
                    logger.info('没有笔记, 跳过')
                    return page

                section_list = await section_list.all()
                result = []
                for section in section_list:
                    url = await self.get_child_visible_locator(section, 'section section_list _url')
                    url_text = await url.get_attribute('href')
                    url_text = f'https://www.xiaohongshu.com{url_text}'
                    img = await self.get_child_visible_locator(section, 'section section_list _img')
                    img_text = await img.get_attribute('src')
                    title = await self.get_child_visible_locator(section, 'section section_list _title')
                    title_text = await title.inner_text()
                    like = await self.get_child_visible_locator(section, 'section section_list _like')
                    like_text = await like.inner_text()
                    result.append({
                        'url': url_text,
                        'cover': img_text,
                        'title': title_text,
                        'count': like_text
                    })
                    logger.info(f'{user_name_text} 点赞量: {like_text}, 标题: {title_text}')
                with open(f'{self.data_path.download_public}/data_{user_name_text}.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
        return page

    async def channel_comment(self, page: Page,
                              ids: Tuple[str, ...] = (),
                              times: int = 3,
                              actions: Tuple[str, ...] = (),
                              mention: Tuple[str, ...] = (),
                              shuffle: bool = False,
                            ) -> Page:
        """ 评论指定用户的笔记 """
        logger.info('评论指定用户的笔记')
        me_name = await self.get_me_name(page)
        for number in ids:
            number = number.strip()
            page, state = await self.enter_homepage(page, number)
            if state:
                no_section = await self.get_locator(page, 'section no_section')
                section_list = await self.get_locator(page, 'section section_list')
                section_index = await self.wait_first_locator([no_section, section_list.first])
                if section_index == 0:
                    logger.info(f'用户: {number} 没有笔记, 跳过')
                    return page

                section_list = await section_list.all()
                times = min(int(times), len(section_list))
                if shuffle:
                    sections = random.sample(section_list, times)
                else:
                    sections = section_list[:times]
                for section in sections:
                    img = await self.get_child_visible_locator(section, 'section section_list _img')
                    await img.click()
                    await self.handle_comment(page, actions, mention, me_name)
                    logger.info('关闭窗口')
                    await self.wait_medium(page)
                    await self.ensure_close(page)
        return page


__all__ = ['XhsChannel']
