import os
import json
from datetime import datetime
from typing import Tuple
from playwright.async_api import Page
from functools import partial

from mediamate.config import config
from mediamate.platforms.base import BaseLocator
from mediamate.platforms.helpers import remove_at_users, add_message_to_list, message_reply
from mediamate.utils.schemas import MediaInfo
from mediamate.tools.api_market.chat import Chat
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class XhsHomepage(BaseLocator):
    """ 处理笔记列表页 """
    def __init__(self, info: MediaInfo):
        super().__init__(info)
        self.register_ai()

    def register_ai(self):
        """ 添加AI功能 """
        api_key = config.get('302__APIKEY')
        model = config.get('302__LLM')
        if api_key:
            chat = Chat(api_key, model)
            common_config = self.account_info.common
            if common_config.get('ai_prompt_content_filter'):
                callback = partial(message_reply, chat, common_config.get('ai_prompt_content_filter'))
                self.register_content_filter(callback)
            if common_config.get('ai_prompt_user_filter'):
                callback = partial(message_reply, chat, common_config.get('ai_prompt_user_filter'))
                self.register_user_filter(callback)
            if common_config.get('ai_prompt_content_comment'):
                callback = partial(message_reply, chat, common_config.get('ai_prompt_content_comment'))
                self.register_content_comment(callback)
            if common_config.get('ai_prompt_content_comment_reply'):
                callback = partial(message_reply, chat, common_config.get('ai_prompt_content_comment_reply'))
                self.register_content_comment_reply(callback)
            if common_config.get('ai_prompt_content_chat'):
                callback = partial(message_reply, chat, common_config.get('ai_prompt_content_chat'))
                self.register_content_chat(callback)
            if common_config.get('ai_prompt_content_chat_reply'):
                callback = partial(message_reply, chat, common_config.get('ai_prompt_content_chat_reply'))
                self.register_content_chat_reply(callback)

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

    async def get_me_name(self, page) -> str:
        """ 获取自己的用户名, 防止对别人重复评论 """
        steps = ('me',)
        await self.ensure_step_page(page, steps)
        user_name = await self.get_visible_locator(page, 'me user_name')
        user_name = await user_name.inner_text()
        return user_name.strip()

    async def ensure_close(self, page: Page) -> Page:
        """  """
        close = await self.get_locator(page, 'section close')
        if await close.is_visible():
            await close.click()
            await close.wait_for(state='hidden')
        return page

    async def handle_comment(self, page: Page, actions: Tuple[str, ...] = (), mention: Tuple[str, ...] = (), me_name: str = '') -> Page:
        """
        评论笔记:
        1. 已点赞/收藏过滤
        2. 判断内容是否感兴趣过滤
        3. 点赞/收藏
        4. 展开评论区(暂时不要)
        5. 已评论过的不再评论
        5. 只保留有效评论内容做参考
        6. 进行评论
        7. 保留笔记链接/内容和用户链接/评论数据
        8. 滑动鼠标, 下拉评论区
        9. 感兴趣多停留一会儿

        子回复暂不处理
        """
        logger.info('处理评论')
        # 先等评论加载出来
        no_comment = await self.get_locator(page, 'section no_comment')
        comment_list = await self.get_locator(page, 'section comment_list')
        comment_index = await self.wait_first_locator([no_comment, comment_list.first])

        like_button = await self.get_locator(page, 'section like')
        like = await self.get_locator(page, 'section like not')
        liked = await self.get_locator(page, 'section like clicked')
        like_index = await self.wait_first_locator([like, liked])

        collect_button = await self.get_locator(page, 'section collect')
        collect = await self.get_locator(page, 'section collect not')
        collected = await self.get_locator(page, 'section collect clicked')
        collect_index = await self.wait_first_locator([collect, collected])

        close = await self.get_visible_locator(page, 'section close')
        if like_index == 1 or collect_index == 1:
            # 已处理过
            logger.info('该笔记已查看过')
            await close.click()
            return page

        records = {}    # 记录保存到本地
        records['url'] = page.url
        title = await self.get_locator(page, 'section title')
        desc = await self.get_locator(page, 'section desc')
        dt = await self.get_locator(page, 'section dt')
        records['title'] = ''
        records['desc'] = ''
        dt_text = await dt.inner_text()
        records['dt'] = dt_text.strip()

        message_list = []
        note = {}
        if await title.is_visible():
            title_text = await title.inner_text()
            note['笔记标题'] = title_text.strip()
            records['title'] = note['笔记标题']
            logger.info(f"笔记标题: {title_text.strip()}")
        if await desc.is_visible():
            desc_text = await desc.inner_text()
            desc_text = remove_at_users(desc_text)
            desc_text = desc_text.strip()
            if not desc_text:
                logger.info(f'笔记描述为空, 忽略')
                await close.click()
                return page

            note['笔记描述'] = desc_text
            records['desc'] = note['笔记描述']
            logger.info(f"笔记描述: {desc_text}")

        message_list = add_message_to_list(note, message_list)
        if not await self.media_content_filter(content=[note]):
            logger.info('对该笔记不感兴趣, 忽略')
            await close.click()
            return page

        if like_index == 0 and '点赞' in actions:
            await like_button.click()
        if collect_index == 0 and '收藏' in actions:
            await collect_button.click()

        temp_record_list = []
        if comment_index == 1:  # 有评论
            loading = await self.get_locator(page, 'section loading')
            the_end = await self.get_locator(page, 'section the_end')
            comment_list_count = 0
            while True:
                comment_list_all = await comment_list.all()
                for comment in comment_list_all[comment_list_count:]:
                    record = {}  # 保留record数据
                    author = await self.get_child_locator(comment, 'section comment_list _author')
                    content = await self.get_child_locator(comment, 'section comment_list _content')
                    like = await self.get_child_locator(comment, 'section comment_list _like')
                    reply = await self.get_child_locator(comment, 'section comment_list _reply')

                    if await author.is_hidden() and await content.is_hidden():
                        continue
                    author_text = await author.inner_text()
                    if me_name and me_name == author_text.strip():
                        logger.info('页面已评论过, 不再评论')
                        await close.click()
                        return page

                    content_text = await content.inner_text()
                    content_text = remove_at_users(content_text)
                    content_text = content_text.strip()
                    if not content_text:
                        logger.info('评论内容为空, 忽略')
                        continue
                    author_href = await author.get_attribute('href')
                    author_url = 'https://www.xiaohongshu.com' + author_href
                    record['author'] = author_text.strip()
                    record['author_url'] = author_url
                    record['author_content'] = content_text
                    like_text = await like.inner_text()
                    like_text = like_text.strip()
                    if '万' in like_text:
                        like_num = int(float(like_text.replace('万', ''))) * 10000
                    elif '赞' in like_text:
                        like_num = 0
                    else:
                        like_num = int(like_text)
                    reply_text = await reply.inner_text()
                    reply_text = reply_text.strip()
                    if '万' in reply_text:
                        reply_num = int(float(reply_text.replace('万', ''))) * 10000
                    elif '回复' in reply_text:
                        reply_num = 0
                    else:
                        reply_num = int(reply_text)
                    record['like'] = like_num
                    record['reply'] = reply_num
                    logger.info(f"游客评论: {content_text}")
                    note = {}
                    note['游客评论'] = content_text
                    # 只保留有效评论(小红书的评论真少)
                    if like_num > 1 or reply_num > 1:
                        message_list = add_message_to_list(note, message_list)
                    temp_record_list = add_message_to_list(record, temp_record_list)
                comment_list_count += len(comment_list_all)
                if len(temp_record_list) > self.default_data_length or await the_end.is_visible():
                    break
                # 每次向下滑动700px
                await comment_list.last.hover()
                await self.wheel(page, delta_y=700)
                # 等待消息加载完毕
                await loading.wait_for(state='hidden')
        if '评论' in actions:
            comment_text = await self.media_content_comment(message_list[:5])
            comment_text = comment_text.replace('\n', ' ')
            comment_button = await self.get_visible_locator(page, 'section comment')
            await comment_button.click()
            logger.info(f'回复内容: {comment_text}')
            await page.keyboard.type(comment_text)
            for sb in mention:
                await page.keyboard.type(f'@{sb}')
                # 小红书的@功能及不稳定, 放弃治疗
                await self.wait_short(page)
                mention = await self.get_locator(page, 'section mention')
                if await mention.is_visible():
                    await mention.click()
                    await mention.wait_for(state='hidden')
            await page.keyboard.press('Enter')
            temp_record_list = add_message_to_list({'发表评论': comment_text}, temp_record_list)
        records['comments'] = temp_record_list
        records_file = os.path.join(self.data_path.download_public, f"{datetime.today().strftime('%Y-%m-%d')}.csv")
        with open(records_file, 'a', encoding='utf-8') as f:
            f.write('\n\n\n')
            json.dump(records, f, ensure_ascii=False, indent=4)
        await close.click()
        return page

    async def handle_comment_reply(self, page: Page) -> Page:
        """
        回复评论:
        1. 日期大于days直接过滤
        2. 自己的评论不回复
        3. 展开评论区
        4. 已回复过不回复
        """
        logger.info('回复评论')
        # 先等评论加载出来
        no_comment = await self.get_locator(page, 'section no_comment')
        comment_list = await self.get_locator(page, 'section comment_list')
        comment_index = await self.wait_first_locator([no_comment, comment_list.first])
        # 关闭页面
        close = await self.get_visible_locator(page, 'section close')
        if comment_index == 0:
            logger.info('没有评论, 忽略')
            await close.click()
            return page

        title = await self.get_locator(page, 'section title')
        desc = await self.get_locator(page, 'section desc')
        dt = await self.get_locator(page, 'section dt')
        # 超过限定日期的不看
        dt_text = await dt.inner_text()
        dt_text = dt_text.strip()
        logger.info(f'日期: {dt_text}')
        keywords = {'今天', '分钟', '小时', '刚刚'}
        if any(keyword in dt_text for keyword in keywords):
            days_diff = 1
        elif '昨天' in dt_text:
            days_diff = 2
        elif '天前' in dt_text:
            days_diff = int(dt_text.split(' ')[0]) + 1
        elif len(dt_text) == 5:
            month, day = int(dt_text[:2]), int(dt_text[-2:])
            date_difference = datetime.today().replace(month=month, day=day) - datetime.today()
            days_diff = abs(date_difference.days) + 1
        elif len(dt_text) == 9:
            year, month, day = int(dt_text[:4]), int(dt_text[6:8]), int(dt_text[-2:])
            date_difference = datetime.today().replace(year=year, month=month, day=day) - datetime.today()
            days_diff = abs(date_difference.days) + 1
        else:
            logger.error('日期解析错误, 忽略')
            days_diff = 0
        if days_diff > self.default_reply_comment_days:
            logger.info(f'日期距离今天超过{self.default_reply_comment_days}天, 忽略')
            await close.click()
            return page

        message_list = []
        note = {}
        if await title.is_visible():
            title_text = await title.inner_text()
            note['自己的笔记标题'] = title_text.strip()
        if await desc.is_visible():
            desc_text = await desc.inner_text()
            desc_text = remove_at_users(desc_text)
            desc_text = desc_text.strip()
            if not desc_text:
                logger.info('笔记描述为空, 忽略')
                await close.click()
                return page
            note['自己的笔记描述'] = desc_text
            logger.info(f'笔记描述: {desc_text}')
        loading = await self.get_locator(page, 'section loading')
        the_end = await self.get_locator(page, 'section the_end')

        comment_list_count = 0
        while True:
            comment_list_all = await comment_list.all()
            for comment in comment_list_all[comment_list_count:]:
                show_more = await self.get_child_locator(comment, 'section comment_list _show_more')
                if await show_more.is_visible():
                    await show_more.click()

                author_self = await self.get_child_locator(comment, 'section comment_list _self')
                content = await self.get_child_locator(comment, 'section comment_list _content')
                if await author_self.is_visible():
                    logger.info('自己的评论, 忽略')
                    continue
                reply_list = await self.get_child_locator(comment, 'section comment_list _reply_list')
                if await reply_list.count() > 0:
                    reply_author_self = await self.get_child_locator(comment, 'section comment_list _reply_list _reply_self')
                    if await reply_author_self.count():
                        logger.info('已经回复过, 忽略')
                        continue

                if await content.is_hidden():
                    logger.info('评论内容不可见, 忽略')
                    continue

                content_text = await content.inner_text()
                content_text = remove_at_users(content_text)
                content_text = content_text.strip()
                if not content_text:
                    logger.info('评论内容为空, 忽略')
                    continue
                logger.info(f"评论内容: {content_text}")
                note['游客评论'] = content_text
                comment_text = await self.media_content_comment_reply([note])
                comment_text = comment_text.replace('\n', ' ')
                comment_input = await self.get_visible_locator(page, 'section input')
                await comment_input.click()
                logger.info(f'回复内容: {comment_text}')
                await page.keyboard.type(comment_text)
                message_list = add_message_to_list(note.copy(), message_list)
                await page.keyboard.press('Enter')
            comment_list_count += len(comment_list_all)
            if len(message_list) > self.default_reply_comment_length or await the_end.is_visible():
                break
            # 每次向下滑动700px
            await comment_list.last.hover()
            await self.wheel(page, delta_y=700)
            # 等待消息加载完毕
            await loading.wait_for(state='hidden')
        await close.click()
        return page
