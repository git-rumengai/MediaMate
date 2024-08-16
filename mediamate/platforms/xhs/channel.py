import asyncio
import re
import os
import json
import random
from datetime import datetime
from typing import Tuple, Callable, List, Dict, Coroutine, Any
from playwright.async_api import Page, Locator

from mediamate.utils.schemas import MediaLoginInfo
from mediamate.utils.log_manager import log_manager
from mediamate.config import config
from mediamate.platforms.base import BaseLocator
from mediamate.utils.const import OPEN_URL_TIMEOUT
from mediamate.platforms.verify import RotateVerify


logger = log_manager.get_logger(__file__)


class XhsChannel(BaseLocator):
    """ 主页互动 """
    def __init__(self):
        super().__init__()
        self.verify = RotateVerify()

    def init(self, info: MediaLoginInfo):
        """  """
        elements_path = f'{config.PROJECT_DIR}/platforms/static/elements/xhs/base.yaml'
        super().init(elements_path)
        return self

    async def ensure_page(self, page: Page) -> Page:
        """ 页面重新加载, 所有步骤要重新执行 """
        loading = page.locator(self.parser.get_xpath('common loading'))
        if await loading.is_visible():
            await loading.wait_for(state='hidden')
        refresh = page.locator(self.parser.get_xpath('common refresh'))
        if await refresh.is_visible():
            await refresh.click()
            await refresh.wait_for(state='hidden')
        return page

    async def ensure_close(self, page: Page) -> Page:
        """  """
        close = await self.get_locator(page, 'explore close')
        if await close.is_visible():
            await close.click()
            await close.wait_for(state='hidden')
        return page

    async def get_me_name(self, page) -> str:
        """  """
        steps = ('explore me',)
        await self.ensure_step_page(page, steps)
        user_name = await self.get_visible_locator(page, 'explore me user_name')
        user_name = await user_name.inner_text()
        return user_name.strip()

    async def channel_me(self, page: Page, days: int=7, callback: Callable[..., Coroutine[Any, Any, str]] = None) -> Page:
        """ 进入个人页回复评论 """
        logger.info('进入个人页')
        await self.get_me_name(page)
        close = await self.get_locator(page, 'explore close')

        note = await self.get_visible_locator(page, 'explore me note')
        await note.click()
        notes_list = await self.get_visible_locators(page, 'explore me note_list')
        notes_list = await notes_list.all()
        for note in notes_list:
            onlyme = await self.get_child_locator(note, 'explore me note_list _onlyme')
            if await onlyme.is_visible():
                logger.info('仅自己可见')
                continue

            await self.ensure_close(page)
            logger.info('点击封面')
            cover = await self.get_child_locator(note, 'explore me note_list _cover')
            await cover.click()
            detail = await self.get_visible_locator(page, 'explore detail')
            # 超过限定日期的不看
            dt = await self.get_child_visible_locator(detail, 'explore detail _datetime')
            dt_text = await dt.inner_text()
            logger.info(f'日期: {dt_text}')
            if '今天' not in dt_text and '昨天' not in dt_text and '天前' not in dt_text:
                date_pattern = r'(\d{2})-(\d{2})'
                match = re.search(date_pattern, dt_text)
                if not match:
                    logger.info('日期匹配错误, 忽略')
                    continue
                month, day = map(int, match.groups())
                current_year = datetime.now().year
                extracted_date = datetime(current_year, month, day)
                today = datetime.now()
                date_difference = extracted_date - today
                if abs(date_difference.days) > days:
                    logger.info(f'日期距离今天超过{days}天')
                    break

            title = await self.get_child_visible_locator(detail, 'explore detail _title')
            title_text = await title.inner_text()
            logger.info(f'标题: {title_text}')
            desc = await self.get_child_visible_locator(detail, 'explore detail _desc')
            desc_text = await desc.inner_text()
            logger.info(f'描述: {desc_text}')
            messages = [{'title': title_text}, {'describe': desc_text}]

            comments_list = await self.get_child_locator(detail, 'explore detail _comments_list')
            first_comments_list = await comments_list.all()
            # 先把该展开的都展开
            if len(first_comments_list) > 0:
                for comments in first_comments_list:
                    expand = await self.get_child_locator(comments, 'explore detail _comments_list _expand')
                    if await expand.is_visible():
                        logger.info('展开')
                        await expand.click()
            second_comments_list = await comments_list.all()
            if len(second_comments_list) > 0:
                for comments in second_comments_list:
                    me = await self.get_child_locator(comments, 'explore detail _comments_list _me')
                    me = await me.all()
                    if len(me) > 0:
                        logger.info('已回复过')
                        messages = []
                        continue
                    author = await self.get_child_visible_locator(comments, 'explore detail _comments_list _author')
                    author_text = await author.inner_text()
                    logger.info(f'作者: {author_text}')
                    content = await self.get_child_visible_locator(comments, 'explore detail _comments_list _content')
                    content_text = await content.inner_text()
                    logger.info(f'评论: {content_text}')
                    expand = await self.get_child_locator(comments, 'explore detail _comments_list _expand')
                    if await expand.is_visible():
                        logger.info('展开')
                        await expand.click()
                    messages.append({
                        f'user_{author_text}': content_text
                    })
                    inner_comments = await self.get_child_locator(comments, 'explore detail _comments_list _inner_list')
                    inner_comments = await inner_comments.all()
                    if len(inner_comments) > 0:
                        for inner_comment in inner_comments:
                            inner_author = await self.get_child_visible_locator(inner_comment, 'explore detail _comments_list _inner_list _author')
                            inner_author_text = await inner_author.inner_text()
                            inner_content = await self.get_child_visible_locator(inner_comment, 'explore detail _comments_list _inner_list _content')
                            inner_content_text = await inner_content.inner_text()
                            logger.info(f'回复作者: {inner_author_text}. 回复评论: {inner_content_text}')
                            messages.append({f'user_{inner_author_text}': inner_content_text})
                    if not messages:
                        continue
                    reply = await callback(messages=messages)
                    reply_button = await self.get_child_locator(comments, 'explore detail _comments_list _reply')
                    if await reply_button.is_visible():
                        await reply_button.click()
                    comment_input = await self.get_visible_locator(page, 'explore input')
                    await comment_input.click()
                    await comment_input.fill(reply)
                    await page.keyboard.press('Enter')
        # 关闭页面
        if await close.is_visible():
            await close.click()
        return page

    async def handle_note(self, page: Page,
                              me_name: str,
                              actions: Tuple[str, ...] = (),
                              mention: Tuple[str, ...] = (),
                              callback: Callable[..., Coroutine[Any, Any, str]] = None) -> Page:
        """  """
        detail = await self.get_visible_locator(page, 'explore detail')
        if '点赞' in actions:
            logger.info('点赞')
            like = await self.get_visible_locator(page, 'explore like')
            await like.click()
        if '收藏' in actions:
            logger.info('收藏')
            collect = await self.get_visible_locator(page, 'explore collect')
            await collect.click()
        if '评论' in actions:
            logger.info('评论')
            messages = []
            # 不一定有标题/描述
            desc = await self.get_child_locator(detail, 'explore detail _desc')
            if await desc.is_visible():
                desc_text = await desc.inner_text()
                messages.append({'describe': desc_text})
                logger.info(f'内容: {desc_text}')
            title = await self.get_child_locator(detail, 'explore detail _title')
            if await title.is_visible():
                title_text = await title.inner_text()
                logger.info(f'标题: {title_text}')
                messages.append([{'title': title_text}])
            # 可能存在
            comments_list = await self.get_child_locator(detail, 'explore detail _comments_list')
            loading = await self.get_child_locator(detail, 'explore loading')
            if await loading.is_visible():
                await loading.wait_for(state='hidden')
            comments_list = await comments_list.all()

            for comments in comments_list:
                # 只需要看最外层的评论
                author = await self.get_child_locator(comments, 'explore detail _comments_list _author')
                content = await self.get_child_locator(comments, 'explore detail _comments_list _content')
                if await author.is_visible() and await content.is_visible():
                    author_text = await author.inner_text()
                    content_text = await content.inner_text()
                    logger.info(f'用户: {author_text}, 评论: {content_text}')
                    messages.append({f'参考评论: ': content_text})
                    if author_text.strip() == me_name:
                        logger.info('该内容已评论过')
                        messages = []
                        break
            if not messages:
                return page

            reply = await callback(messages=messages)
            logger.info('点击回复')
            comment = await self.get_visible_locator(page, 'explore comment')
            await comment.click()
            comment_input = await self.get_visible_locator(page, 'explore input')
            await comment_input.click()
            logger.info(f'回复内容: {reply}')
            await page.keyboard.type(reply)
            for sb in mention:
                await page.keyboard.type(f'@{sb}')
                # 小红书的@功能及不稳定, 放弃治疗
                await asyncio.sleep(0.1)
                mention = await self.get_locator(page, 'explore mention')
                if await mention.is_visible():
                    await mention.click()
                    await mention.wait_for(state='hidden')
            return page

    async def channel_explore(self, page: Page,
                              topics: Tuple[str, ...],
                              times: int = 1,
                              actions: Tuple[str, ...] = (),
                              mention: Tuple[str, ...] = (),
                              callback: Callable[..., Coroutine[Any, Any, str]] = None) -> Page:
        """ 随机浏览发现页 """
        logger.info('进入发现页')
        me_name = await self.get_me_name(page)
        steps = ('explore',)
        await self.ensure_step_page(page, steps)

        type_list = await self.get_visible_locators(page, 'explore topic_list')
        section_list = await self.get_visible_locators(page, 'explore section_list')
        actions = actions or ('点赞',)

        type_list = await type_list.all()
        for topic in type_list:
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
                cover = await self.get_child_visible_locator(section, 'explore section_list _cover')
                await cover.click()
                await self.handle_note(page, me_name, actions=actions, mention=mention, callback=callback)
                close = await self.get_visible_locator(page, 'explore close')
                logger.info('关闭窗口')
                await close.click()
                await close.wait_for(state='hidden')
        return page

    async def enter_homepage(self, page: Page, number: str) -> bool:
        """ 通过搜索进入用户主页 """
        search_url = f'https://www.xiaohongshu.com/search_result?keyword={number}&source=unknown&search_type=user'
        await page.goto(search_url, timeout=OPEN_URL_TIMEOUT)
        await self.ensure_page(page)
        search = await self.get_visible_locator(page, 'search')
        await search.click()
        # 不要点击跳转, 通过链接直接跳转
        user = await self.get_visible_locator(page, 'search user')
        url = await user.get_attribute('href')
        full_url = f'https://www.xiaohongshu.com{url}'
        await page.goto(full_url, timeout=OPEN_URL_TIMEOUT)
        return True

    async def channel_download(self, page: Page, data_dir: str, ids: Tuple[str, ...] = ()) -> Page:
        """ 下载指定用户笔记(不翻页) """
        logger.info('下载指定用户笔记')
        steps = ('explore', )
        await self.ensure_step_page(page, steps)

        for number in ids:
            number = number.strip()
            if await self.enter_homepage(page, number):
                user_name = await self.get_visible_locator(page, 'search user_name')
                user_name_text = await user_name.inner_text()
                user_name_text = user_name_text.strip()
                section_one = await self.get_locator(page, 'search section_one')
                if not await section_one.is_visible():
                    logger.info(f'用户没有笔记: {number}')
                    return page
                section_list = await self.get_visible_locators(page, 'search section_list')
                section_list = await section_list.all()
                result = []
                for section in section_list:
                    url = await self.get_child_visible_locator(section, 'search section_list _url')
                    url_text = await url.get_attribute('href')
                    url_text = f'https://www.xiaohongshu.com{url_text}'
                    cover = await self.get_child_visible_locator(section, 'search section_list _cover')
                    cover_text = await cover.get_attribute('src')
                    title = await self.get_child_visible_locator(section, 'search section_list _title')
                    title_text = await title.inner_text()
                    count = await self.get_child_visible_locator(section, 'search section_list _count')
                    count_text = await count.inner_text()
                    result.append({
                        'url': url_text,
                        'cover': cover_text,
                        'title': title_text,
                        'count': count_text
                    })
                    logger.info(f'{user_name_text} 点赞量: {count_text}, 标题: {title_text}')
                with open(f'{data_dir}/data_{user_name_text}.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
        return page

    async def channel_comment(self, page: Page,
                              ids: Tuple[str, ...] = (),
                              times: int = 3,
                              actions: Tuple[str, ...] = (),
                              mention: Tuple[str, ...] = (),
                              shuffle: bool = False,
                              callback: Callable[..., Coroutine[Any, Any, str]] = None
                            ) -> Page:
        """ 评论指定用户的笔记 """
        logger.info('评论指定用户的笔记')
        me_name = await self.get_me_name(page)
        for number in ids:
            number = number.strip()
            if await self.enter_homepage(page, number):
                section_one = await self.get_locator(page, 'search section_one')
                if not await section_one.is_visible():
                    logger.info(f'用户没有笔记: {number}')
                    return page
                section_list = await self.get_visible_locators(page, 'search section_list')
                section_list = await section_list.all()
                times = min(int(times), len(section_list))
                if shuffle:
                    sections = random.sample(section_list, times)
                else:
                    sections = section_list[:times]
                for section in sections:
                    cover = await self.get_child_visible_locator(section, 'search section_list _cover')
                    await cover.click()
                    await self.handle_note(page, me_name, actions=actions, mention=mention, callback=callback)
                    close = await self.get_visible_locator(page, 'explore close')
                    logger.info('关闭窗口')
                    await close.click()
                    await close.wait_for(state='hidden')
        return page


__all__ = ['XhsChannel']
