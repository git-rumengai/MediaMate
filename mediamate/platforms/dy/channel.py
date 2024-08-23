import json
import random
from typing import Tuple
from playwright.async_api import Page

from mediamate.utils.const import DEFAULT_URL_TIMEOUT
from mediamate.utils.log_manager import log_manager
from mediamate.platforms.dy.homepage import DyHomepage


logger = log_manager.get_logger(__file__)


class DyChannel(DyHomepage):
    """ 主页互动 """
    async def channel_discover(self,
                               page: Page,
                               topics: Tuple[str, ...],
                               times: int = 1,
                               actions: Tuple[str, ...] = (),
                               mention: Tuple[str, ...] = ()
                               ):
        """ 抖音主页随机刷 """
        me_name = await self.get_me_name(page)
        await self.ensure_player_close(page)
        if '/discover' not in page.url:
            steps = ('discover', )
            await self.ensure_step_page(page, steps)
        logger.info('进入主页')
        hot = await self.get_locator(page, 'discover hot')

        for item in topics:
            lis = []
            if await hot.is_visible():
                if item == '挑战榜':
                    logger.info(f'点击 挑战榜')
                    rank = await self.get_visible_locator(page, 'discover challenge')
                    await rank.click()
                    await self.wait_short(page)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
                elif item == '热榜':
                    logger.info(f'进入 热榜')
                    rank = await self.get_visible_locator(page, 'discover hot')
                    await rank.click()
                    await self.wait_short(page)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
                elif item == '娱乐榜':
                    logger.info(f'进入 娱乐榜')
                    rank = await self.get_visible_locator(page, 'discover game')
                    await rank.click()
                    await self.wait_short(page)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
                elif item == '社会榜':
                    logger.info(f'进入 社会榜')
                    rank = await self.get_visible_locator(page, 'discover social')
                    await rank.click()
                    await self.wait_short(page)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
            else:
                if item == '首页':
                    logger.info(f'进入 首页')
                    ul = await self.get_visible_locators(page, 'discover container_list')
                    container_list = await ul.all()
                    # 过滤直播
                    for li in container_list:
                        live = await self.get_child_locator(li, 'discover container_list _live')
                        if await live.is_visible():
                            continue
                        lis.append(li)

            times = min(int(times), len(lis))
            lis = lis[:times]
            for li in lis:
                await li.click()
                page = await self.handle_comment(page, actions, mention, me_name)
        return page

    async def enter_homepage(self, page: Page, number: str) -> Tuple[Page, bool]:
        """ 通过搜索进入用户主页 """
        # search_url = f'https://www.douyin.com/search/{number}?type=user'
        # await page.goto(search_url, timeout=DEFAULT_URL_TIMEOUT)

        await self.ensure_page(page)
        search = await self.get_visible_locator(page, 'search')
        button = await self.get_visible_locator(page, 'search button')
        await search.click()
        await page.keyboard.type(number)

        # 点击按钮，打开新页面
        async with page.expect_popup() as popup_info:
            await button.click()
        new_page = await popup_info.value
        await self.ensure_page(new_page)
        await new_page.wait_for_load_state()
        page = new_page

        user = await self.get_visible_locator(page, 'search user')
        await user.click()
        user_list = await self.get_visible_locators(page, 'search user_list')
        user_list = await user_list.all()

        # 这里通过链接跳转, 不要更换page
        url = await self.get_child_visible_locator(user_list[0], 'search user_list _url')
        url_text = await url.get_attribute('href')
        await page.goto(f'https:{url_text}', timeout=DEFAULT_URL_TIMEOUT)

        user_name = await self.get_locator(page, 'section username')
        user_name_text = await user_name.inner_text()
        logger.info(f'进入主页: {user_name_text}')
        no_section = await self.get_locator(page, 'section no_section')
        section_list = await self.get_locator(page, 'section section_list')
        section_index = await self.wait_first_locator([no_section, section_list.first])
        if section_index == 0:
            logger.info('没有作品, 忽略')
            return page, False
        private = await self.get_locator(page, 'section private')
        if await private.is_visible():
            logger.info('私密账号, 忽略')
            return page, False

        no_more = await self.get_locator(page, 'section no_more')
        count = 0
        while True:
            count += 1
            if await no_more.is_visible():
                break
            await self.scroll(page)
            logger.info(f'滚动页面加载更多数据: {count}')
            await self.wait_medium(page)
            section_list_all = await section_list.all()
            if len(section_list_all) > self.default_data_length:
                break
        return page, True

    async def channel_download(self, page: Page, ids: Tuple[str, ...] = ()) -> Page:
        """ 下载用户主页视频地址 """
        logger.info('下载用户主页视频地址')
        for number in ids:
            number = number.strip()

            page, state = await self.enter_homepage(page, number)
            if state:
                user_name = await self.get_visible_locator(page, 'section username')
                user_name_text = await user_name.inner_text()
                user_name_text = user_name_text.strip()

                section_list = await self.get_visible_locators(page, 'section section_list')
                section_list_all = await section_list.all()
                items = []
                for section in section_list_all:
                    url = await self.get_child_visible_locator(section, 'section section_list _url')
                    img = await self.get_child_visible_locator(section, 'section section_list _img')
                    like = await self.get_child_visible_locator(section, 'section section_list _like')
                    title = await self.get_child_visible_locator(section, 'section section_list _title')
                    url_text = await url.get_attribute('href')
                    url_text = f'https://www.douyin.com{url_text.strip()}'
                    img_text = await img.get_attribute('src')
                    img_text = f'https:{img_text.strip()}'
                    like_text = await like.inner_text()
                    like_text = like_text.strip()
                    title_text = await title.inner_text()
                    title_text = title_text.strip()
                    logger.info(f'{user_name_text} 点赞量: {like_text}, 标题: {title_text}')
                    items.append({
                        'url': url_text,
                        'cover': img_text,
                        'user_name': user_name_text,
                        'like': like_text,
                        'title': title_text
                    })
                with open(f'{self.data_path.download_public}/data_{user_name_text}.json', 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=4)
        return page

    async def channel_comment(self,
                              page: Page,
                              ids: Tuple[str, ...] = (),
                              times: int = 3,
                              actions: Tuple[str, ...] = (),
                              mention: Tuple[str, ...] = (),
                              shuffle: bool = False,
                            ) -> Page:
        """ 在某人主页视频评论区添加评论, 默认选择前3个视频 """
        logger.info('给指定用户视频评论')
        me_name = await self.get_me_name(page)
        for number in ids:
            page, state = await self.enter_homepage(page, number)
            if state:
                section_list = await self.get_visible_locators(page, 'section section_list')
                section_list_all = await section_list.all()
                times = min(int(times), len(section_list_all))
                if shuffle:
                    section_list_all = random.sample(section_list_all, times)
                else:
                    section_list_all = section_list_all[:times]
                for section in section_list_all:
                    img = await self.get_child_visible_locator(section, 'section section_list _img')
                    await img.click()
                    page = await self.handle_comment(page, actions, mention, me_name)
        return page

    async def channel_target(self,
                             page: Page,
                             ids: Tuple[str, ...],
                             times: int = 3,
                             batch: int = 1,
                             shuffle: bool = False,
                             ) -> Page:
        """ 在某用户主页视频评论区私聊并关注目标用户, 默认选择前3个视频, 每个视频私聊1个用户 """
        logger.info('在用户视频评论区私聊并关注目标用户')
        me_name = await self.get_me_name(page)
        for number in ids:
            page, state = await self.enter_homepage(page, number)
            if state:
                section_list = await self.get_visible_locators(page, 'section section_list')
                section_list_all = await section_list.all()
                if shuffle:
                    section_list_all = random.sample(section_list_all, times)
                else:
                    section_list_all = section_list_all[:times]
                for section in section_list_all:
                    await self.ensure_player_close(page)
                    img = await self.get_child_visible_locator(section, 'section section_list _img')
                    await img.click()
                    await self.handle_chat_target(page, me_name, batch)
                    await self.wait_short(page)
        return page


__all__ = ['DyChannel']
