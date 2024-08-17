import asyncio
import os
from typing import Optional
from playwright.async_api import Page, async_playwright, Playwright

from mediamate.utils.schemas import MediaLoginInfo
from mediamate.utils.log_manager import log_manager
from mediamate.utils.enums import LocatorType
from mediamate.platforms.dy.uploader import DyUploader
from mediamate.platforms.dy.downloader import DyDownloader
from mediamate.platforms.dy.operator import DyOperator
from mediamate.platforms.dy.channel import DyChannel
from mediamate.platforms.base import BaseClient
from mediamate.config import config
from mediamate.utils.const import DEFAULT_REPLY


logger = log_manager.get_logger(__file__)


class DyClient(BaseClient):
    def __init__(self):
        super().__init__()
        self.uploader = DyUploader()
        self.downloader = DyDownloader()
        self.operator = DyOperator()
        self.channel = DyChannel()

    def init(self, info: MediaLoginInfo):
        """  """
        super().init(info)
        self.uploader.init(info)
        self.downloader.init(info)
        self.operator.init(info)
        self.channel.init(info)
        return self

    async def start_base(self, playwright: Optional[Playwright] = None):
        """启动基础流程，支持内部与外部 Playwright 上下文管理器"""
        async def _start(playwright):
            context, page = await self.login(playwright, LocatorType.HOME)
            if not await self.check_login_state(page):
                logger.info(f'账户未登录, 请先登录: {self.login_info.account}')
                return
            page = await self.start_discover(page)
            page = await self.start_download(page)
            page = await self.start_comment(page)
            page = await self.start_follow(page)
            # 停止跟踪并保存文件
            trace_path = f'{config.DATA_DIR}/browser/{self.login_info.platform.value}/{self.login_info.account}/trace_base.zip'
            await context.tracing.stop(path=trace_path)
            logger.info('可进入查看跟踪结果: https://trace.playwright.dev/')

        if playwright:
            await _start(playwright)
        else:
            async with async_playwright() as playwright:
                await _start(playwright)

    async def start_creator(self, playwright: Optional[Playwright] = None):
        """启动基础流程，支持内部与外部 Playwright 上下文管理器"""
        async def _start(playwright):
            context, page = await self.login(playwright, LocatorType.CREATOR)
            if not await self.check_login_state(page):
                logger.info(f'账户未登录, 请先登录: {self.login_info.account}')
                return
            if self.login_info.creator.get('upload'):
                await self.start_upload(page)
            await self.start_mydata(page)
            await self.start_operate(page)
            # 停止跟踪并保存文件
            trace_path = f'{config.DATA_DIR}/browser/{self.login_info.platform.value}/{self.login_info.account}/trace_creator.zip'
            await context.tracing.stop(path=trace_path)
            logger.info('可进入查看跟踪结果: https://trace.playwright.dev/')

        if playwright:
            await _start(playwright)
        else:
            async with async_playwright() as playwright:
                await _start(playwright)

    async def start_mydata(self, page: Page):
        """  """
        downloader = self.login_info.creator.get('downloader')
        if downloader:
            if downloader.get('manage'):
                page = await self.downloader.click_manage(page)
            if downloader.get('datacenter'):
                page = await self.downloader.click_datacenter(page)
            if downloader.get('creative_guidance'):
                page = await self.downloader.click_creative_guidance(page, tuple(downloader.get('creative_guidance')))
            if downloader.get('排行榜'):
                page = await self.downloader.click_billboard(page, tuple(downloader.get('billboard')))
            await asyncio.sleep(3)
        return page

    async def start_operate(self, page: Page):
        """  """
        operator_comment = self.login_info.creator.get('operator_comment')
        if operator_comment:
            days = operator_comment.get('days', 7)
            default = operator_comment.get('default', DEFAULT_REPLY)
            prompt = operator_comment.get('prompt')
            partial_reply = self.get_reply_func(default, prompt)
            page = await self.operator.click_comment(page, days, partial_reply)

            operator_chat = self.login_info.creator.get('operator_chat')
            default = operator_comment.get('default', DEFAULT_REPLY)
            prompt = operator_chat.get('prompt')
            partial_reply = self.get_reply_func(default, prompt)
            page = await self.operator.click_chat(page, partial_reply)
            await asyncio.sleep(3)
        return page

    async def start_discover(self, page: Page) -> Page:
        """ 随机浏览首页信息 """
        discover = self.login_info.base.get('discover')
        if discover:
            topics = discover.get('topics', ())
            times = discover.get('times', 1)
            actions = discover.get('actions', ())
            mention = discover.get('mention', ())
            default = discover.get('default', DEFAULT_REPLY)
            prompt = discover.get('prompt')
            partial_reply = self.get_reply_func(default, prompt)
            page = await self.channel.channel_discover(page, topics=topics, times=times, actions=actions, mention=mention, callback=partial_reply)
        return page

    async def start_download(self, page: Page) -> Page:
        """ 下载指定用户的视频信息 """
        download = self.login_info.base.get('download')
        if download:
            ids = download.get('ids', ())
            data_dir = download.get('data_dir', 'videos')
            full_dir = f'{config.DATA_DIR}/download/{self.login_info.platform.value}/{self.login_info.account}/{data_dir}'
            os.makedirs(full_dir, exist_ok=True)
            page = await self.channel.channel_download(page, full_dir, ids=ids)
        return page

    async def start_comment(self, page: Page) -> Page:
        """ 评论指定用户的视频 """
        comment = self.login_info.base.get('comment')
        if comment:
            ids = comment.get('ids', ())
            times = comment.get('times', 1)
            actions = comment.get('actions', ())
            mention = comment.get('mention', ())
            shuffle = comment.get('shuffle', False)
            default = comment.get('default', DEFAULT_REPLY)
            prompt = comment.get('prompt')
            partial_reply = self.get_reply_func(default, prompt)
            page = await self.channel.channel_comment(page, ids=ids, times=times, actions=actions, mention=mention, shuffle=shuffle, callback=partial_reply)
        return page

    async def start_follow(self, page: Page) -> Page:
        """ 从指定用户的评论区添加好友 """
        follow = self.login_info.base.get('follow')
        if follow:
            ids = follow.get('ids', ())
            times = follow.get('times', 1)
            batch = follow.get('batch', 1)
            shuffle = follow.get('shuffle', False)
            default = follow.get('default', DEFAULT_REPLY)
            prompt = follow.get('prompt')
            partial_reply = self.get_reply_func(default, prompt)
            page = await self.channel.channel_follow(page, msg=default, ids=ids, times=times, batch=batch, shuffle=shuffle, callback=partial_reply if prompt else None)
        return page

    async def upload_text(self, page: Page) -> Optional[Page]:
        """  """
        title = self.uploader.metadata_config.get('标题')
        describe = self.uploader.metadata_config.get('描述')
        labels = self.uploader.metadata_config.get('标签')
        location = self.uploader.metadata_config.get('地点')
        theme = self.uploader.metadata_config.get('贴纸')
        wait_minute = self.uploader.metadata_config.get('图片超时报错', 3)
        download = self.uploader.metadata_config.get('允许保存')
        download = True if download == '是' else False
        try:
            page = await self.uploader.click_note(page)
            page = await self.uploader.click_upload_image(page, wait_minute)
            page = await self.uploader.write_title(page, title)
            page = await self.uploader.write_describe(page, describe, labels)
            page = await self.uploader.set_location(page, location)
            page = await self.uploader.set_theme(page, theme)
            page = await self.uploader.set_download(page, download)
            page = await self.uploader.set_permission(page)
            page = await self.uploader.set_time(page)
            page = await self.uploader.click_publish(page)
            logger.info('图文发布成功, 5s自动返回')
            await asyncio.sleep(3)
            return page
        except Exception as e:
            logger.error(f'上传图文报错: {e}')

    async def upload_video(self, page: Page) -> Optional[Page]:
        """  """
        title = self.uploader.metadata_config.get('标题')
        describe = self.uploader.metadata_config.get('描述')
        labels = self.uploader.metadata_config.get('标签')
        location = self.uploader.metadata_config.get('地点')
        theme = self.uploader.metadata_config.get('贴纸')
        wait_minute = self.uploader.metadata_config.get('视频超时报错', 10)
        download = self.uploader.metadata_config.get('允许保存')
        download = True if download == '是' else False
        try:
            page = await self.uploader.click_note(page)
            page = await self.uploader.click_upload_video(page, wait_minute)
            page = await self.uploader.write_title(page, title)
            page = await self.uploader.write_describe(page, describe, labels)
            page = await self.uploader.set_location(page, location)
            page = await self.uploader.set_theme(page, theme)
            page = await self.uploader.set_download(page, download)
            page = await self.uploader.set_permission(page)
            page = await self.uploader.set_time(page)
            page = await self.uploader.click_publish(page)
            logger.info('视频发布成功, 3s自动返回')
            await asyncio.sleep(3)
            return page
        except Exception as e:
            logger.error(f'上传视频报错: {e}')


__all__ = ['DyClient']
