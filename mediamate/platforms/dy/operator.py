import asyncio
import re
import os
import random
from datetime import datetime, timedelta
from typing import Optional, Callable, List, Dict, Coroutine, Any
from playwright.async_api import Page

from mediamate.utils.schemas import MediaLoginInfo
from mediamate.utils.const import OPEN_URL_TIMEOUT
from mediamate.utils.log_manager import log_manager
from mediamate.config import config
from mediamate.platforms.base import BaseLocator

logger = log_manager.get_logger(__file__)


class DyOperator(BaseLocator):
    """ 下载数据 """
    def __init__(self):
        super().__init__()
        self.download_data_dir = ''
        self.download_user_dir = ''

    def init(self, info: MediaLoginInfo):
        """  """
        elements_path = f'{config.PROJECT_DIR}/platforms/static/elements/dy/creator.yaml'
        super().init(elements_path)

        self.download_data_dir = f'{config.DATA_DIR}/download/douyin/{info.account}'
        self.download_user_dir = f'{self.download_data_dir}/user_data'
        os.makedirs(self.download_user_dir, exist_ok=True)
        return self

    async def ensure_page(self, page: Page) -> Page:
        """ 页面重新加载, 所有步骤要重新执行 """
        home_loading = page.locator(self.parser.get_xpath('common home_loading'))
        if await home_loading.is_visible():
            logger.info('页面加载中...')
            await home_loading.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')
        page_loading = page.locator(self.parser.get_xpath('common page_loading'))
        if await page_loading.is_visible():
            logger.info('页面加载中...')
            await page_loading.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')
        page_wrong = page.locator(self.parser.get_xpath('common page_wrong'))
        if await page_wrong.is_visible():
            logger.info('页面出错, 重新加载...')
            await page.reload(timeout=OPEN_URL_TIMEOUT)
        tips_warning = page.locator(self.parser.get_xpath('common tips_warning'))
        if await page_wrong.is_visible():
            logger.info('页面警告提示...')
            await tips_warning.click()
            await tips_warning.wait_for(state='hidden')
        return page

    async def comment_handle_dialog(self, page: Page, callback: Callable[..., Coroutine[Any, Any, str]] = None):
        """  """
        describe = await self.get_locator(page, 'revenue describe')
        describe_text = await describe.inner_text()
        comment_list = await self.get_visible_locators(page, 'revenue comment comment_list')
        first_comments = await comment_list.all()
        # 先把该展开的都展开
        for comment in first_comments:
            expand = await self.get_child_locator(comment, 'revenue comment comment_list expand')
            if await expand.is_visible():
                await expand.click()
                await expand.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')
        second_comments = await comment_list.all()
        for comment in second_comments:
            username = await self.get_child_locator(comment, 'revenue comment comment_list username')
            content = await self.get_child_locator(comment, 'revenue comment comment_list content')
            username_text = await username.inner_text()
            if await content.is_visible():
                content_text = await content.inner_text()
            else:
                logger.info('忽略文字评论为空')
                continue
            if not content_text:
                continue
            logger.info(f'username: {username_text}, content: {content_text}')
            author_span = username.locator('span')
            if await author_span.is_visible():
                logger.info('忽略作者评论')
                continue
            messages = []
            if '无视频描述' not in describe_text:
                messages.append({'video describe': describe_text})
            messages.append({f'user_{username_text}': content_text})
            child = await self.get_child_locator(comment, 'revenue comment comment_list inner_comment')
            child_lis = await child.all()
            for li in child_lis:
                grandson_username = await self.get_child_locator(li, 'revenue comment comment_list inner_comment inner_username')
                grandson_content = await self.get_child_locator(li, 'revenue comment comment_list inner_comment inner_content')
                messages.append({f'user_{grandson_username}': grandson_content})
                author_span = grandson_username.locator('span')
                if await author_span.is_visible():
                    logger.info('忽略评论中作者的评论')
                    messages = []
                    break
            if messages:
                reply = await callback(messages=messages)
                reply_button = await self.get_child_visible_locator(comment, 'revenue comment comment_list reply')
                await reply_button.click()
                reply_textarea = await self.get_child_visible_locator(comment, 'revenue comment comment_list textarea')
                await reply_textarea.click()
                await reply_textarea.type(reply)
                send_button = await self.get_child_locator(comment, 'revenue comment comment_list send')
                await send_button.wait_for(state='attached')
                await send_button.click()
                logger.info('评论已回复')
                await asyncio.sleep(random.random() * 3)

    async def click_comment(self, page: Page, days: int = 7, callback: Callable[..., Coroutine[Any, Any, str]] = None) -> Optional[Page]:
        """  """
        logger.info('处理评论')
        steps = ('home', 'home text_datacenter', 'revenue', 'revenue comment', 'revenue comment text_comment')
        await self.ensure_step_page(page, steps)
        no_video = page.locator(self.parser.get_xpath('revenue comment no_video'))
        if await no_video.is_visible():
            logger.info('你还没有发布视频')
            return page

        select = await self.get_visible_locator(page, 'revenue comment select')
        await select.click()
        container_list = await self.get_visible_locators(page, 'revenue comment container_list')
        container_list = await container_list.all()

        for container in container_list:
            dt = await self.get_child_visible_locator(container, 'revenue comment container_list _datetime')
            comments = await self.get_child_visible_locator(container, 'revenue comment container_list _comments')
            dt_text = await dt.inner_text()
            pattern = r"发布于(\d{4}年\d{2}月\d{2}日) (\d{2}:\d{2})"
            match = re.search(pattern, dt_text.strip())
            if not match:
                continue
            # 提取的日期和时间
            date_str = match.group(1)
            datetime_str = f"{date_str.replace('年', '-').replace('月', '-').replace('日', '')}"
            extracted_datetime = datetime.strptime(datetime_str, "%Y-%m-%d")
            current_datetime = datetime.now()
            # 判断是否超过 num 天
            if current_datetime - extracted_datetime > timedelta(days=days):
                break
            comments_text = await comments.inner_text()
            count = int(comments_text.strip())
            if count == 0:
                continue
            await container.click()
            await self.comment_handle_dialog(page, callback)
            await select.click()
        await container_list[0].click()
        return page

    async def chat_wait_loading(self, page: Page):
        """ 等待消息加载 """
        chat_loading = page.locator(self.parser.get_xpath('common chat_loading'))
        if await chat_loading.is_visible():
            logger.info('消息数据加载中...')
            await chat_loading.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')

    async def chat_send_message(self, page: Page, reply: str):
        if reply:
            send_button = await page.query_selector('div.chat-input--3G9Sm')
            if send_button:
                await send_button.type(reply)
                await send_button.click()
                await page.keyboard.press('Enter')
                logger.info(f'消息回复成功')

    async def click_chat(self, page: Page, callback: Callable[..., Coroutine[Any, Any, str]] = None) -> Optional[Page]:
        """  """
        logger.info('处理私信')
        steps = ('home', 'home text_datacenter', 'revenue', 'revenue message', 'revenue message all')
        await self.ensure_step_page(page, steps)

        friend = await self.get_visible_locator(page, 'revenue message friend')
        stranger = await self.get_visible_locator(page, 'revenue message stranger')
        messages_list = await self.get_visible_locators(page, 'revenue message messages_list')
        messages_list = await messages_list.all()
        for index, message_list in enumerate(messages_list):
            if index in [0, 3]:
                continue
            if index == 1:
                logger.info('处理朋友私信')
                await friend.click()
            else:
                logger.info('处理陌生人私信')
                await stranger.click()
            child_message_list = await self.get_child_locator(message_list, 'revenue message messages_list _message_list')
            child_message_list = await child_message_list.all()
            for message in child_message_list:
                unread = await self.get_child_locator(message, 'revenue message messages_list _message_list _unread')
                if await unread.is_visible():
                    unread_text = await unread.inner_text()
                    if unread_text:
                        logger.info('存在未读消息')
                        await message.click()
                        await self.chat_wait_loading(page)
                        dialogue_list = await self.get_visible_locators(page, 'revenue message dialogue_list')
                        dialogue_list = await dialogue_list.all()
                        last_attribute = await dialogue_list[-1].get_attribute('class')
                        if 'is-me' in last_attribute:
                            logger.info('消息已回复过')
                            continue
                        items = []
                        text_user = await self.get_visible_locator(page, 'revenue message text_user')
                        text_user_text = await text_user.inner_text()
                        for dialogue in dialogue_list:
                            content = await self.get_child_locator(dialogue, 'revenue message dialogue_list _content')
                            if await content.is_visible():
                                dialogue_text = await content.inner_text()
                                if '可以开始聊天了' not in dialogue_text:
                                    items.append({f'user_{text_user_text.strip()}': dialogue_text.strip()})
                        reply = await callback(items)
                        message_input = await self.get_visible_locator(page, 'revenue message input_text')
                        await message_input.click()
                        await message_input.type(reply)
                        await page.keyboard.press('Enter')
                        return_button = await self.get_visible_locator(page, 'revenue message retrun')
                        await return_button.click()
        return page


__all__ = ['DyOperator']
