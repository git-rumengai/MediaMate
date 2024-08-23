import os
import re
import json
from datetime import datetime
from typing import Tuple
from functools import partial
from playwright.async_api import Page

from mediamate.platforms.base import BaseLocator
from mediamate.utils.const import DEFAULT_URL_TIMEOUT
from mediamate.utils.log_manager import log_manager
from mediamate.platforms.helpers import remove_at_users, add_message_to_list, message_reply
from mediamate.utils.schemas import MediaInfo
from mediamate.tools.api_market.chat import Chat
from mediamate.config import config, ConfigManager


logger = log_manager.get_logger(__file__)


class DyHomepage(BaseLocator):
    """ 处理视频列表页 """
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
        tips_move = page.locator(self.parser.get_xpath('common tips_move'))
        if await tips_move.is_visible():
            logger.info('出现滚动视频弹窗提示')
            await tips_move.hover()
            await self.wheel(page, 0, 200)

        tips_default = page.locator(self.parser.get_xpath('common tips_default'))
        if await tips_default.is_visible():
            logger.info('出现默认设置弹窗提示')
            await tips_default.click()

        page_loading = page.locator(self.parser.get_xpath('common page_loading'))
        if await page_loading.is_visible():
            logger.info('出现视频加载弹窗提示')
            await page_loading.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='hidden')

        # 通过确认消息图标确认页面加载完毕
        chat = page.locator(self.parser.get_xpath('chat'))
        await chat.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='visible')
        return page

    async def get_me_name(self, page) -> str:
        """ 获取自己的用户名, 防止对别人重复评论 """
        me = await self.get_visible_locator(page, 'me')
        await me.hover()
        me_name = await self.get_visible_locator(page, 'me _name')
        user_name_text = await me_name.inner_text()
        return user_name_text.strip()

    async def ensure_stop_auto(self, page: Page) -> Page:
        """  """
        # 首先关闭连播
        await self.get_visible_locator(page, 'player auto')
        auto_clicked = await self.get_locator(page, 'player auto clicked')
        if await auto_clicked.is_visible():
            logger.info('关闭连播')
            await auto_clicked.click()
            await auto_clicked.wait_for(state='hidden')
        return page

    async def ensure_player_close(self, page: Page) -> Page:
        """ 确保关闭播放页面 """
        close = await self.get_locator(page, 'player close')
        if await close.is_visible() and '/user/' not in page.url and 'recommend=1' not in page.url:
            await close.click()
            await close.wait_for(state='hidden')
        return page

    async def ensure_chat_exit(self, page: Page) -> Page:
        """ 确保关闭消息框 """
        close = await self.get_locator(page, 'chat close')
        if await close.is_visible():
            await close.click()
            await close.wait_for(state='hidden')
        chat_exit = await self.get_locator(page, 'chat exit')
        if await chat_exit.is_visible():
            await chat_exit.click()
            await chat_exit.wait_for(state='hidden')
        return page

    async def handle_comment(self, page: Page, actions: Tuple[str, ...] = (), mention: Tuple[str, ...] = (), me_name: str = '') -> Page:
        """
        处理评论:
        1. 已点赞/收藏过滤
        2. 判断内容是否感兴趣过滤
        3. 点赞/收藏
        4. 展开评论区(暂时不要)
        5. 已评论过的不再评论
        5. 只保留有效评论内容做参考
        6. 进行评论
        7. 保留视频链接/内容和用户链接/评论数据
        8. 滑动鼠标, 下拉评论区
        9. 感兴趣多停留一会儿

        子回复暂不处理
        """
        logger.info('处理评论')
        await self.ensure_stop_auto(page)
        # 先等评论数加载出来
        comment = await self.get_locator(page, 'player comment')
        comment_number = await self.get_child_visible_locator(comment, 'player comment _number')
        comment_number = await comment_number.inner_text()
        if '抢首评' in comment_number:
            comment_number = 0
        elif '万' in comment_number:
            comment_number = int(float(comment_number.replace('万', ''))) * 10000
        else:
            comment_number = int(comment_number)
        comment_button = await self.get_child_visible_locator(comment, 'player comment _button')
        await comment_button.click()

        like = await self.get_locator(page, 'player like')
        like_button = await self.get_child_locator(like, 'player like _button')
        like_not = await self.get_child_locator(like, 'player like _not')
        like_clicked = await self.get_child_locator(like, 'player like _clicked')
        like_number = await self.get_child_locator(like, 'player like _number')
        like_number = await like_number.inner_text()
        like_index = await self.wait_first_locator([like_not, like_clicked])

        collect = await self.get_locator(page, 'player collect')
        collect_button = await self.get_child_locator(collect, 'player collect _button')
        collect_not = await self.get_child_locator(collect, 'player collect _not')
        collect_clicked = await self.get_child_locator(collect, 'player collect _clicked')
        collect_number = await self.get_child_locator(collect, 'player collect _number')
        collect_number = await collect_number.inner_text()
        collect_index = await self.wait_first_locator([collect_not, collect_clicked])

        close = await self.get_visible_locator(page, 'player close')
        if like_index == 1 or collect_index == 1:
            # 已处理过
            logger.info('该视频已处理过')
            await close.click()
            return page

        records = {}    # 记录保存到本地
        records['url'] = page.url
        author = await self.get_locator(page, 'player author')
        author = await author.inner_text()
        desc = await self.get_locator(page, 'player desc')
        author_url = await self.get_locator(page, 'player author_url')

        records['desc'] = ''
        records['author'] = author.strip()
        records['author_url'] = await author_url.get_attribute('href')
        records['like_number'] = like_number.strip()
        records['collect_number'] = collect_number.strip()
        records['comment_number'] = comment_number

        message_list = []
        video = {}
        if await desc.is_visible():
            desc_text = await desc.inner_text()
            desc_text = remove_at_users(desc_text)
            desc_text = desc_text.strip()
            if not desc_text:
                logger.info(f'视频描述内容为空, 忽略')
                await close.click()
                return page
            video['视频描述'] = desc_text
            records['desc'] = video['视频描述']
            logger.info(f"视频描述: {desc_text}")

        message_list = add_message_to_list(video, message_list)
        if not await self.media_content_filter(content=[video]):
            logger.info('对该视频不感兴趣, 忽略')
            await close.click()
            return page

        if like_index == 0 and '点赞' in actions:
            await like_button.click()
        if collect_index == 0 and '收藏' in actions:
            await collect_button.click()

        temp_record_list = []
        if comment_number > 0:  # 有评论
            comment_tab = await self.get_visible_locator(page, 'player comment_tab')
            await comment_tab.click()
            comment_list = await self.get_visible_locators(page, 'player comment_list')
            the_end = await self.get_locator(page, 'player the_end')

            comment_list_count = 0
            while True:
                comment_list_all = await comment_list.all()
                for comment in comment_list_all[comment_list_count:]:
                    record = {}  # 保留record数据
                    author = await self.get_child_locator(comment, 'player comment_list _author')

                    author_name = await self.get_child_locator(author, 'player comment_list _author _name')
                    author_url = await self.get_child_locator(author, 'player comment_list _author _url')
                    content = await self.get_child_locator(author, 'player comment_list _author _content')
                    like = await self.get_child_locator(author, 'player comment_list _author _like')

                    if await author_name.is_hidden() or await content.is_hidden():
                        continue
                    author_name_text = await author_name.inner_text()
                    if me_name and me_name == author_name_text.strip():
                        logger.info('页面已评论过, 不再评论')
                        await close.click()
                        return page

                    content_text = await content.inner_text()
                    content_text = remove_at_users(content_text)
                    content_text = content_text.strip()
                    if not content_text:
                        logger.info('评论内容为空, 忽略')
                        continue
                    author_href = await author_url.get_attribute('href')
                    author_url = 'https:' + author_href
                    record['author'] = author_name_text.strip()
                    record['author_url'] = author_url

                    record['author_content'] = content_text
                    like_text = await like.inner_text()
                    if '万' in like_text:
                        like_num = int(float(like_text.replace('万', ''))) * 10000
                    else:
                        like_num = int(like_text)
                    record['like'] = like_num
                    logger.info(f"游客评论: {content_text}")
                    video = {}
                    video['游客评论'] = content_text
                    # 只保留有效评论
                    if like_num > 1:
                        message_list = add_message_to_list(video, message_list)
                    temp_record_list = add_message_to_list(record, temp_record_list)
                comment_list_count += len(comment_list_all)
                if len(temp_record_list) > self.default_data_length or await the_end.is_visible():
                    break
                # 每次向下滑动700px
                await comment_list.last.hover()
                await self.wheel(page, delta_y=700)

        if '评论' in actions:
            comment_text = await self.media_content_comment(message_list[:5])
            # 评论中不能有换行符
            comment_text = comment_text.replace('\n', ' ')
            comment_input = await self.get_visible_locator(page, 'player input')
            await comment_input.click()
            logger.info(f'回复内容: {comment_text}')
            await page.keyboard.type(comment_text)
            for sb in mention:
                await page.keyboard.type(f'@{sb}')
                mention_first = await self.get_locator(page, 'player mention_first')
                await self.wait_short(page)
                if await mention_first.is_visible():
                    await page.keyboard.press('Enter')
                    await mention_first.wait_for(state='hidden')
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
        1. 日期大于 default_reply_comment_days 直接过滤
        2. 自己的评论不回复
        3. 展开评论区
        4. 已回复过不回复
        """
        # 先等评论加载出来
        logger.info('回复评论')
        await self.ensure_stop_auto(page)
        comment = await self.get_locator(page, 'player comment')
        comment_number = await self.get_child_visible_locator(comment, 'player comment _number')
        comment_number = await comment_number.inner_text()
        if '抢首评' in comment_number:
            comment_number = 0
        elif '万' in comment_number:
            comment_number = int(float(comment_number.replace('万', ''))) * 10000
        else:
            comment_number = int(comment_number)
        comment_button = await self.get_child_visible_locator(comment, 'player comment _button')
        await comment_button.click()

        close = await self.get_visible_locator(page, 'player close')
        if comment_number == 0:
            logger.info('没有评论, 忽略')
            await close.click()
            return page

        desc = await self.get_locator(page, 'player desc')
        dt = await self.get_locator(page, 'player dt')
        # 超过限定日期的不看
        dt_text = await dt.inner_text()
        dt_text = dt_text.strip().replace('· ', '')
        logger.info(f'日期: {dt_text}')
        keywords = {'今天', '分钟', '小时', '刚刚'}
        if any(keyword in dt_text for keyword in keywords):
            days_diff = 1
        elif '昨天' in dt_text:
            days_diff = 2
        elif '天前' in dt_text:
            days_diff = int(dt_text.replace('天前', ''))
        elif '周前' in dt_text:
            days_diff = int(dt_text.replace('周前', '')) * 7 + 1
        else:
            pattern = re.compile(r'(\d{4}年)?(\d{1,2}月\d{1,2}日)')
            match = pattern.search(dt_text)
            if match:
                today = datetime.today()
                year_str = match.group(1)
                month_day_str = match.group(2)
                if not year_str:
                    year_str = f"{today.year}年"
                full_date_str = year_str + month_day_str
                date_obj = datetime.strptime(full_date_str, '%Y年%m月%d日')
                # 计算距离今天的天数
                days_diff = (date_obj - today).days + 1
            else:
                logger.error('日期解析错误, 忽略')
                days_diff = 0
        if days_diff > self.default_reply_comment_days:
            logger.info(f'日期距离今天超过{self.default_reply_comment_days}天, 忽略')
            await close.click()
            return page

        message_list = []
        video = {}
        if await desc.is_visible():
            desc_text = await desc.inner_text()
            desc_text = remove_at_users(desc_text)
            desc_text = desc_text.strip()
            if not desc_text:
                logger.info('视频描述内容为空, 忽略')
                await close.click()
                return page
            video['自己的视频描述'] = desc_text.strip()

        comment_tab = await self.get_visible_locator(page, 'player comment_tab')
        await comment_tab.click()
        comment_list = await self.get_visible_locators(page, 'player comment_list')
        the_end = await self.get_locator(page, 'player the_end')

        comment_list_count = 0
        while True:
            comment_list_all = await comment_list.all()
            for comment in comment_list_all[comment_list_count:]:
                show_more = await self.get_child_locator(comment, 'player comment_list _expand')
                if await show_more.is_visible():
                    await show_more.click()

                author = await self.get_child_locator(comment, 'player comment_list _author')
                author_self = await self.get_child_locator(author, 'player comment_list _author _self')
                if await author_self.is_visible():
                    logger.info('自己的评论, 忽略')
                    continue
                content = await self.get_child_locator(author, 'player comment_list _author _content')
                reply_list = await self.get_child_locator(comment, 'player comment_list _reply_list')
                if await reply_list.count() > 0:
                    reply_author_self = await self.get_child_locator(reply_list, 'player comment_list _reply_list _self')
                    if await reply_author_self.count() > 0:
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
                video['游客评论'] = content_text
                comment_text = await self.media_content_comment_reply([video])
                # 评论中不能有换行符
                comment_text = comment_text.replace('\n', ' ')
                comment_input = await self.get_visible_locator(page, 'player input')
                await comment_input.click()
                await comment_input.clear()
                logger.info(f'回复内容: {comment_text}')
                await page.keyboard.type(comment_text)
                message_list = add_message_to_list(video.copy(), message_list)
                await page.keyboard.press('Enter')
            comment_list_count += len(comment_list_all)
            if len(message_list) > self.default_reply_comment_length or await the_end.is_visible():
                break
            # 每次向下滑动700px
            await comment_list.last.hover()
            await self.wheel(page, delta_y=700)
        # 关闭页面
        await close.click()
        return page

    async def enter_chat(self, page: Page) -> Page:
        """
        选择并进入私信
        1. 判断出现私信
        2. 鼠标悬停, 选择私信, 退出会话, 鼠标悬停...
        3. 过滤days天内的私信
        """
        chat = await self.get_visible_locator(page, 'chat')
        chat_count = await self.get_child_locator(chat, 'chat _count')
        chat_button = await self.get_child_locator(chat, 'chat _butthon')
        if await chat_count.is_visible():
            await chat_button.hover()
            chat_list = await self.get_visible_locators(page, 'chat chat_list')
            chat_list_all = await chat_list.all()
            for msg in chat_list_all:
                msg_count = await self.get_child_locator(msg, 'chat chat_list _count')
                if await msg_count.is_visible():
                    await msg.click()
                    await self.handle_chat_reply(page)
                    break
        return page

    async def handle_chat_reply(self, page: Page) -> Page:
        """
        处理聊天:
        1. 判断好友/陌生人/群聊
        2. 判断是否已回复
        3. 保留私信记录
        4. 判断是否已回复
        5. 点击关注
        """
        myself = '自己'
        other = '对方'
        username = await self.get_visible_locator(page, 'chat username')
        username_text = await username.inner_text()
        logger.info(f'正在处理私信: {username_text.strip()}')
        group = await self.get_locator(page, 'chat group')
        if await group.is_visible():
            logger.info('群聊信息, 忽略')
            await self.ensure_chat_exit(page)
            return page
        follow = await self.get_locator(page, 'chat follow')
        dialog_list = await self.get_visible_locators(page, 'chat dialog_list')
        dialog_list_all = await dialog_list.all()
        message = []
        for dialog in dialog_list_all[::-1]:
            content = await self.get_child_locator(dialog, 'chat dialog_list _content')
            bg = await self.get_child_locator(dialog, 'chat dialog_list _bg')
            if await content.is_hidden():   # 无内容可能是图片
                continue
            if await bg.count() == 0:    # 无背景为系统消息
                continue
            position = await self.get_child_locator(dialog, 'chat dialog_list _position')
            position_style = await position.get_attribute('style')
            identity = myself if 'right' in position_style else other
            content_text = await content.inner_text()
            content_text = content_text.strip()
            if not content_text:
                # 空消息
                continue
            message.append({identity: content_text})
        chat_input = await self.get_visible_locator(page, 'chat input')
        if len(message) == 0 and self.default_chat_message:
            logger.info(f'只有系统消息: 忽略')
            await self.ensure_chat_exit(page)
            return page
        elif message[-1].keys() == myself:
            logger.info('已回复过信息, 忽略')
            await self.ensure_chat_exit(page)
            return page
        else:
            if await follow.is_visible():
                await follow.click()
            reply_text = await self.media_content_chat_reply(message[-5:])
            # 评论中不能有换行符
            reply_text = reply_text.replace('\n', ' ')
            await chat_input.click()
            await page.keyboard.type(reply_text)
            await page.keyboard.press('Enter')
            message.append({myself: reply_text})
        chat_file = ConfigManager(self.data_path.download_personal_chat_file)
        await chat_file.set(username_text, message)
        await self.ensure_chat_exit(page)

    async def force_send_message(self, page: Page) -> bool:
        """ 主动发私信 """
        username = await self.get_visible_locator(page, 'section username')
        username_text = await username.inner_text()
        logger.info(f'主动私信: {username_text.strip()}')

        await self.ensure_page(page)
        follow = await self.get_visible_locator(page, 'section follow')
        follow_button = await self.get_child_locator(follow, 'section follow _button')
        follow_clicked = await self.get_child_locator(follow, 'section follow _clicked')
        if await follow_clicked.is_visible():
            logger.info('用户已关注, 忽略')
            return False
        await follow_button.click()
        await follow_clicked.wait_for(state='visible')
        message = await self.get_visible_locator(page, 'section message')
        await message.click()
        chat_input = await self.get_visible_locator(page, 'chat input')
        await chat_input.click()
        default_chat_message = self.default_chat_message.replace('\n', ' ')
        await page.keyboard.type(default_chat_message)
        await page.keyboard.press('Enter')
        logger.info(f'主动私信已发送: {self.default_chat_message}')
        return True

    async def handle_chat_target(self, page: Page, me_name: str, batch: int = 1) -> Page:
        """
        从评论区寻找目标用户:
        1. 判断是否是目标用户
        2. 点赞并主动发消息
        3. 滑动鼠标, 下拉评论区
        4. 感兴趣多停留一会儿
        子回复暂不处理
        """
        logger.info('从评论区寻找目标用户')
        await self.ensure_stop_auto(page)
        # 先等评论数加载出来
        comment = await self.get_locator(page, 'player comment')
        comment_number = await self.get_child_visible_locator(comment, 'player comment _number')
        comment_number = await comment_number.inner_text()
        if '抢首评' in comment_number:
            comment_number = 0
        elif '万' in comment_number:
            comment_number = int(float(comment_number.replace('万', ''))) * 10000
        else:
            comment_number = int(comment_number)
        comment_button = await self.get_child_visible_locator(comment, 'player comment _button')
        await comment_button.click()
        close = await self.get_visible_locator(page, 'player close')
        if comment_number == 0:
            logger.info('无评论, 忽略')
            await close.click()
            return page

        desc = await self.get_locator(page, 'player desc')
        message_list = []
        video = {}
        if await desc.is_visible():
            desc_text = await desc.inner_text()
            video['视频描述'] = desc_text.strip()
            logger.info(f"视频描述: {desc_text.strip()}")
        message_list.append(video)
        comment_tab = await self.get_visible_locator(page, 'player comment_tab')
        await comment_tab.click()
        comment_list = await self.get_visible_locators(page, 'player comment_list')
        the_end = await self.get_locator(page, 'player the_end')

        count = 0
        user_list = []
        while True:
            comment_list_all = await comment_list.all()
            if len(message_list) > 1:
                # 只保留最后6条消息
                comment_list_all = comment_list_all[-6:]
            for comment in comment_list_all:
                author = await self.get_child_locator(comment, 'player comment_list _author')

                author_name = await self.get_child_locator(author, 'player comment_list _author _name')
                author_url = await self.get_child_locator(author, 'player comment_list _author _url')
                content = await self.get_child_locator(author, 'player comment_list _author _content')

                if await author_name.is_hidden() or await content.is_hidden():
                    continue
                count += 1
                author_name_text = await author_name.inner_text()
                author_name_text = author_name_text.strip()
                if author_name_text in user_list:
                    logger.info(f'用户已私聊过, 忽略')
                    continue
                else:
                    user_list.append(author_name_text)
                content_text = await author_name.inner_text()
                content_text = content_text.strip()
                if not content_text:
                    logger.info(f'评论内容为空, 忽略')
                    continue
                logger.info(f'用户: {author_name_text}, 评论: {content_text}')
                if me_name and me_name == author_name_text:
                    logger.info('评论者是自己, 忽略')
                    continue
                message_list.append({'用户评论': content_text})
                user_filter = await self.media_user_filter(message_list)
                if not user_filter:
                    logger.info('不是目标用户, 忽略')
                    continue

                # 点击按钮，打开新页面
                async with page.expect_popup() as popup_info:
                    await author_url.click()
                new_page = await popup_info.value
                await self.ensure_page(new_page)
                await new_page.wait_for_load_state()
                await self.force_send_message(new_page)
                await new_page.close()

            if count > batch or await the_end.is_visible():
                break

            # 每次向下滑动700px
            await comment_list.last.hover()
            await self.wheel(page, delta_y=700)
        await close.click()
        return page
