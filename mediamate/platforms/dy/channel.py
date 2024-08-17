import asyncio
import os
import json
import random
from typing import Tuple, Callable, List, Dict, Coroutine, Any
from playwright.async_api import Page, Locator

from mediamate.utils.schemas import MediaLoginInfo
from mediamate.utils.const import OPEN_URL_TIMEOUT
from mediamate.utils.log_manager import log_manager
from mediamate.config import config
from mediamate.platforms.verify import MoveVerify
from mediamate.platforms.base import BaseLocator
from mediamate.utils.const import DEFAULT_DATA_LENGTH


logger = log_manager.get_logger(__file__)


class DyChannel(BaseLocator):
    """ 主页互动 """
    def __init__(self):
        super().__init__()
        self.verify = MoveVerify()

    def init(self, info: MediaLoginInfo):
        """  """
        elements_path = f'{config.PROJECT_DIR}/platforms/static/elements/dy/base.yaml'
        super().init(elements_path)
        return self

    async def ensure_page(self, page: Page) -> Page:
        """ 页面重新加载, 所有步骤要重新执行 """
        tips_move = page.locator(self.parser.get_xpath('common tips_move'))
        if await tips_move.is_visible():
            logger.info('出现滚动视频弹窗提示')
            await page.mouse.wheel(0, 200)

        tips_default = page.locator(self.parser.get_xpath('common tips_default'))
        if await tips_default.is_visible():
            logger.info('出现默认设置弹窗提示')
            await tips_default.click()

        page_loading = page.locator(self.parser.get_xpath('common page_loading'))
        if await page_loading.is_visible():
            logger.info('出现视频加载弹窗提示')
            await page_loading.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')

        # 出现过没有hot榜单的现象, 通过确认消息图标确认页面加载完毕
        message_flag = page.locator(self.parser.get_xpath('search message_flag'))
        await message_flag.wait_for(timeout=OPEN_URL_TIMEOUT, state='visible')
        return page

    async def channel_discover(self, page: Page, topics: Tuple[str, ...],
                               times: int = 1,
                               actions: Tuple[str, ...] = (),
                               mention: Tuple[str, ...] = (),
                               callback: Callable[..., Coroutine[Any, Any, str]] = None
                               ):
        """ 抖音主页随机刷 """
        discover = await self.get_visible_locator(page, 'discover')
        await discover.click()
        # 确保页面加载完毕
        await self.ensure_page(page)
        hot = await self.get_locator(page, 'discover hot')
        lis = []
        for item in topics:
            if await hot.is_visible():
                if item == '挑战榜':
                    rank = await self.get_visible_locator(page, 'discover challenge')
                    await rank.click()
                    await page.wait_for_timeout(100)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
                elif item == '热榜':
                    rank = await self.get_visible_locator(page, 'discover hot')
                    await rank.click()
                    await page.wait_for_timeout(100)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
                elif item == '娱乐榜':
                    rank = await self.get_visible_locator(page, 'discover game')
                    await rank.click()
                    await page.wait_for_timeout(100)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
                elif item == '社会榜':
                    rank = await self.get_visible_locator(page, 'discover social')
                    await rank.click()
                    await page.wait_for_timeout(100)
                    ul = await self.get_visible_locators(page, 'discover hot_list')
                    lis = await ul.all()
            else:
                logger.info('页面没有热榜, 忽略')
                if item == '首页':
                    ul = await self.get_visible_locators(page, 'discover container_list')
                    container_list = await ul.all()
                    lis = []
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
                await self.get_visible_locator(page, 'player title')
                page = await self.player_comment(page, actions, mention, callback)
        return page

    async def player_comment(self, page: Page,
                            actions: Tuple[str, ...] = (),
                            mention: Tuple[str, ...] = (),
                            callback: Callable[..., Coroutine[Any, Any, str]] = None
                            ) -> Page:
        """ 视频播放页评论 """
        actions = actions or ('点赞', )
        if '点赞' in actions:
            logger.info('点赞')
            like = await self.get_visible_locator(page, 'player like')
            await like.click()
        if '收藏' in actions:
            logger.info('收藏')
            collect = await self.get_visible_locator(page, 'player collect')
            await collect.click()
        if '评论' in actions:
            logger.info('评论')
            comment = await self.get_visible_locator(page, 'player comment')
            await comment.click()
            title = await self.get_visible_locator(page, 'player title')
            title_text = await title.inner_text()
            messages = [{'title': title_text,}]
            logger.info(f'标题: {title_text}')
            if '抢首评' not in await comment.inner_text():
                text_comment = await self.get_visible_locator(page, 'player comment text_comment')
                text_comment_text = await text_comment.inner_text()
                logger.info(text_comment_text)
                # 确保出现数据
                comments_list = await self.get_visible_locators(page, 'player comment comments_list')
                comments_ = await comments_list.all()
                loading = await self.get_locator(page, 'player comment loading')
                while True:
                    if await loading.is_hidden():
                        break
                    else:
                        comments_ = await comments_list.all()
                        if len(comments_) < DEFAULT_DATA_LENGTH:
                            await page.wait_for_timeout(300)
                        else:
                            break
                for comments in comments_:
                    author = await self.get_child_locator(comments, 'player comment comments_list _author')
                    content = await self.get_child_locator(comments, 'player comment comments_list _content')
                    if await author.is_visible() and await content.is_visible():
                        author_text = await author.inner_text()
                        content_text = await content.inner_text()
                        logger.info(f'用户: {author_text}. 评论: {content_text}')
                        if content_text.strip():
                            message = {f'参考评论: ': content_text.strip()}
                            messages.append(message)

            reply = await callback(messages=messages)
            comment_input = await self.get_visible_locator(page, 'player comment input')
            await comment_input.click()
            await page.keyboard.type(reply)

            for sb in mention:
                await page.keyboard.type(f'@{sb}')
                await self.get_visible_locators(page, 'player comment mention_list')
                await page.keyboard.press('Enter')
            await page.keyboard.press('Enter')
            logger.info(f'评论内容: {reply}')
            close = await self.get_visible_locator(page, 'player comment close')
            await close.click()
            logger.info('点击退出')
            exit = await self.get_visible_locator(page, 'player exit')
            await page.wait_for_timeout(100)
            await exit.click()
            await exit.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')
            logger.info('已关闭')
        if '转发' in actions:
            ...

        return page

    async def enter_homepage(self, page: Page, number: str) -> bool:
        """ 通过搜索进入用户主页 """
        search_url = f'https://www.douyin.com/search/{number}?type=user'
        await page.goto(search_url, timeout=OPEN_URL_TIMEOUT)
        await self.ensure_page(page)
        user_list = await self.get_visible_locators(page, 'search user_list')
        user_list = await user_list.all()
        # 不要校验
        # _number = await self.get_child_visible_locator(user_list[0], 'search user_list _number')
        # _number_text = await _number.inner_text()
        # if _number_text.strip() != number:
        #     logger.info(f'抖音号搜索不存在, 忽略')
        #     return False

        # 这里通过链接跳转, 不要更换page
        url = await self.get_child_visible_locator(user_list[0], 'search user_list _url')
        url_text = await url.get_attribute('href')
        await page.goto(f'https:{url_text}', timeout=OPEN_URL_TIMEOUT)

        user_name = await self.get_visible_locator(page, 'search user_name')
        user_name = await user_name.inner_text()
        user_name = user_name.strip()
        text_video = await self.get_visible_locator(page, 'search text_video')
        text_video = await text_video.inner_text()

        video_list = await self.get_visible_locators(page, 'search video_list')
        if int(text_video.strip()) == 0:
            logger.info(f'{user_name} 暂未发表视频')
            return False
        logger.info(f'{user_name} 视频数量: {text_video}')
        no_more = await self.get_locator(page, 'search no_more')
        count = 0
        while True:
            count += 1
            if await no_more.is_visible():
                break
            await self.scroll(page)
            logger.info(f'滚动页面加载更多数据: {count}')
            await page.wait_for_timeout(300)
            videos = await video_list.all()
            if len(videos) > DEFAULT_DATA_LENGTH:
                break
        return True

    async def channel_download(self, page: Page, data_dir: str, ids: Tuple[str, ...] = ()) -> Page:
        """ 下载某人主页视频地址 """
        logger.info('下载主页视频地址')
        for number in ids:
            number = number.strip()
            if await self.enter_homepage(page, number):
                user_name = await self.get_visible_locator(page, 'search user_name')
                user_name = await user_name.inner_text()
                user_name = user_name.strip()
                private = await self.get_locator(page, 'search private')
                if await private.is_visible():
                    logger.info('私密账号, 忽略')
                    continue
                video_list = await self.get_visible_locators(page, 'search video_list')
                video_list = await video_list.all()
                items = []
                for video in video_list:
                    url = await self.get_child_visible_locator(video, 'search video_list _url')
                    cover = await self.get_child_visible_locator(video, 'search video_list _cover')
                    like = await self.get_child_visible_locator(video, 'search video_list _like')
                    title = await self.get_child_visible_locator(video, 'search video_list _title')
                    url_text = await url.get_attribute('href')
                    url_text = f'https://www.douyin.com{url_text.strip()}'
                    cover_text = await cover.get_attribute('src')
                    cover_text = f'https:{cover_text.strip()}'
                    like_text = await like.inner_text()
                    like_text = like_text.strip()
                    title_text = await title.inner_text()
                    title_text = title_text.strip()
                    logger.info(f'{user_name} 点赞量: {like_text}, 标题: {title_text}')
                    items.append({
                        'url': url_text,
                        'cover': cover_text,
                        'user_name': user_name,
                        'like': like_text,
                        'title': title_text
                    })
                with open(f'{data_dir}/data_{user_name}.json', 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=4)
        return page

    async def channel_comment(self, page: Page,
                              ids: Tuple[str, ...] = (),
                              times: int = 3,
                              actions: Tuple[str, ...] = (),
                              mention: Tuple[str, ...] = (),
                              shuffle: bool = False,
                              callback: Callable[..., Coroutine[Any, Any, str]] = None
                            ) -> Page:
        """ 在某人主页视频评论区添加评论, 默认选择前3个视频 """
        logger.info('给指定用户视频评论')
        for number in ids:
            if await self.enter_homepage(page, number):
                private = await self.get_locator(page, 'search private')
                if await private.is_visible():
                    logger.info('私密账号, 忽略')
                    continue
                video_list = await self.get_visible_locators(page, 'search video_list')
                video_list = await video_list.all()
                times = min(int(times), len(video_list))
                if shuffle:
                    video_list = random.sample(video_list, times)
                else:
                    video_list = video_list[:times]
                for video in video_list:
                    await video.click()
                    await self.get_visible_locator(page, 'player title')
                    page = await self.player_comment(page, actions, mention, callback)
        return page

    async def private_message(self, page: Page, msg: str) -> Page:
        """ 处理私信 """
        logger.info('处理私信')
        private = await self.get_locator(page, 'search private')
        if await private.is_visible():
            logger.info('私密账号, 忽略')
            return page
        follow = await self.get_visible_locator(page, 'search follow')
        follow_text = await follow.inner_text()
        if follow_text.strip() == '关注':
            await follow.click()
        elif follow_text.strip() == '编辑资料':
            logger.info('进入了自己的页面')
            return page
        else:
            logger.info(f'用户已经被关注...')
        message = await self.get_visible_locator(page, 'search message')
        await self.get_visible_locator(page, 'search message_flag')
        await message.click()
        message_input = await self.get_visible_locator(page, 'search message_input')
        await message_input.click()
        await page.keyboard.type(msg)
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(300)
        return page

    async def player_chat(self,
                          page: Page,
                          msg: str,
                          batch: int,
                          callback: Callable[..., Coroutine[Any, Any, str]] = None) -> Page:
        """ 通过视频播放评论区寻找目标用户 """
        logger.info('从指定用户的评论中寻找目标用户')
        comment = await self.get_visible_locator(page, 'player comment')
        await comment.click()
        title = await self.get_visible_locator(page, 'player title')
        title_text = await title.inner_text()

        if '抢首评' not in await comment.inner_text():
            text_comment = await self.get_visible_locator(page, 'player comment text_comment')
            text_comment_text = await text_comment.inner_text()
            logger.info(text_comment_text)
            # 确保出现数据
            comments_list = await self.get_visible_locators(page, 'player comment comments_list')
            comments_ = await comments_list.all()
            loading = await self.get_locator(page, 'player comment loading')
            while True:
                if await loading.is_hidden():
                    break
                else:
                    comments_ = await comments_list.all()
                    if len(comments_) < DEFAULT_DATA_LENGTH:
                        await page.wait_for_timeout(300)
                    else:
                        break
            for comments in comments_[:batch]:
                author = await self.get_child_locator(comments, 'player comment comments_list _author')
                content = await self.get_child_locator(comments, 'player comment comments_list _content')
                tag = await self.get_child_locator(comments, 'player comment comments_list _tag')
                if await tag.is_visible():
                    tag_text = await tag.inner_text()
                    if tag_text.strip() == '朋友':
                        logger.info('已经是朋友了')
                        continue
                if await author.is_visible() and await content.is_visible():
                    author_text = await author.inner_text()
                    content_text = await content.inner_text()
                    if content_text.strip():
                        messages = [{'title': title_text, f'user_{author_text}': content_text.strip()}]
                        if callback:
                            reply = await callback(messages=messages)
                            if reply.lower() == 'yes':
                                async with page.expect_popup() as new_page_info:
                                    await author.click()
                                new_page = await new_page_info.value
                                new_page = await self.private_message(new_page, msg)
                                # 关闭新页面
                                await new_page.close()
                        else:
                            async with page.expect_popup() as new_page_info:
                                await author.click()
                            new_page = await new_page_info.value
                            new_page = await self.private_message(new_page, msg)
                            # 关闭新页面
                            await new_page.close()
        else:
            logger.info(f'该视频暂无评论')
        return page

    async def channel_follow(self, page: Page,
                             ids: Tuple[str, ...],
                             msg: str,
                             times: int = 3,
                             batch: int = 1,
                             shuffle: bool = False,
                             callback: Callable[..., Coroutine[Any, Any, str]] = None
                             ) -> Page:
        """ 在某用户主页视频评论区私聊并关注其他用户, 默认选择前3个视频, 每个视频私聊3个用户 """
        for number in ids:
            if await self.enter_homepage(page, number):
                private = await self.get_locator(page, 'search private')
                if await private.is_visible():
                    logger.info('私密账号, 忽略')
                    continue
                video_list = await self.get_visible_locators(page, 'search video_list')
                video_list = await video_list.all()
                if shuffle:
                    video_list = random.sample(video_list, times)
                else:
                    video_list = video_list[:times]
                for video in video_list:
                    await video.click()
                    await self.get_visible_locator(page, 'player title')
                    page = await self.player_chat(page, msg, batch, callback)
                    logger.info('点击退出')
                    exit = await self.get_visible_locator(page, 'player exit')
                    await page.wait_for_timeout(100)
                    await exit.click()
        return page


__all__ = ['DyChannel']
