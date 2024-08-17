import asyncio
import os
from typing import Optional

from playwright.async_api import Page, async_playwright, Playwright
from mediamate.utils.schemas import MediaLoginInfo
from mediamate.utils.log_manager import log_manager
from mediamate.utils.enums import LocatorType
from mediamate.platforms.xhs.uploader import XhsUploader
from mediamate.platforms.xhs.downloader import XhsDownloader
from mediamate.platforms.xhs.channel import XhsChannel
from mediamate.platforms.base import BaseClient
from mediamate.config import config
from mediamate.utils.const import DEFAULT_REPLY


logger = log_manager.get_logger(__file__)


class XhsClient(BaseClient):
    def __init__(self):
        super().__init__()
        self.uploader = XhsUploader()
        self.downloader = XhsDownloader()
        self.channel = XhsChannel()

    def init(self, info: MediaLoginInfo):
        """  """
        super().init(info)
        self.uploader.init(info)
        self.downloader.init(info)
        self.channel.init(info)
        return self

    async def start_base(self, playwright: Optional[Playwright] = None):
        """启动基础流程，支持内部与外部 Playwright 上下文管理器"""
        async def _start(playwright):
            context, page = await self.login(playwright, LocatorType.HOME)
            if not await self.check_login_state(page):
                logger.info(f'账户未登录, 请先登录: {self.login_info.account}')
                return
            try:
                page = await self.start_me(page)
                page = await self.start_explore(page)
                page = await self.start_download(page)
                page = await self.start_comment(page)
            except Exception as e:
                logger.error(e)
            finally:
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
            try:
                if self.login_info.creator.get('upload'):
                    page = await self.start_upload(page)
                page = await self.start_mydata(page)
            except Exception as e:
                logger.error(e)
            finally:
                # 停止跟踪并保存文件
                trace_path = f'{config.DATA_DIR}/browser/{self.login_info.platform.value}/{self.login_info.account}/trace_creator.zip'
                await context.tracing.stop(path=trace_path)
                logger.info('可进入查看跟踪结果: https://trace.playwright.dev/')

        if playwright:
            await _start(playwright)
        else:
            async with async_playwright() as playwright:
                await _start(playwright)

    async def start_mydata(self, page: Page) -> Page:
        """  """
        download = self.login_info.creator.get('download')
        if download:
            page = await self.downloader.click_inspiration(page, topics=tuple(download))
            await page.wait_for_timeout(3000)
        return page

    async def start_me(self, page: Page) -> Page:
        """ 回复自己作品的评论 """
        me = self.login_info.base.get('me')
        if me:
            days = me.get('days', 7)
            default = me.get('default', DEFAULT_REPLY)
            prompt = me.get('prompt')
            partial_reply = self.get_reply_func(default, prompt)
            page = await self.channel.channel_me(page, days=days, callback=partial_reply)
            await page.wait_for_timeout(3000)
        return page

    async def start_explore(self, page: Page) -> Page:
        """  """
        explore = self.login_info.base.get('explore')
        if explore:
            topics = explore.get('topics', ())
            times = explore.get('times', 1)
            actions = explore.get('actions', ())
            mention = explore.get('mention', ())
            default = explore.get('default', DEFAULT_REPLY)
            prompt = explore.get('prompt')
            partial_reply = self.get_reply_func(default, prompt)
            page = await self.channel.channel_explore(page, topics=topics, times=times, actions=actions, mention=mention, callback=partial_reply)
        return page

    async def start_download(self, page: Page) -> Page:
        """  """
        download = self.login_info.base.get('download')
        if download:
            data_dir = download.get('data_dir', 'notes')
            ids = download.get('ids', ())
            full_dir = f'{config.DATA_DIR}/download/{self.login_info.platform.value}/{self.login_info.account}/{data_dir}'
            os.makedirs(full_dir, exist_ok=True)

            page = await self.channel.channel_download(page, data_dir=full_dir, ids=ids)
            await page.wait_for_timeout(3000)
        return page

    async def start_comment(self, page: Page) -> Page:
        """  """
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
            await page.wait_for_timeout(3000)
        return page

    async def upload_text(self, page: Page) -> Optional[Page]:
        """  """
        title = self.uploader.metadata_config.get('标题')
        describe = self.uploader.metadata_config.get('描述')
        labels = self.uploader.metadata_config.get('标签')
        location = self.uploader.metadata_config.get('地点')
        wait_minute = self.uploader.metadata_config.get('图片超时报错', 3)

        page = await self.uploader.click_upload_image(page, wait_minute)
        page = await self.uploader.write_title(page, title)
        page = await self.uploader.write_describe(page, describe, labels)
        page = await self.uploader.set_location(page, location)
        page = await self.uploader.set_permission(page)
        page = await self.uploader.set_time(page)
        page = await self.uploader.click_publish(page)
        logger.info('图文发布成功, 3s自动返回')
        await page.wait_for_timeout(3000)

        return page

    async def upload_video(self, page: Page) -> Optional[Page]:
        """  """
        title = self.uploader.metadata_config.get('标题')
        describe = self.uploader.metadata_config.get('描述')
        labels = self.uploader.metadata_config.get('标签')
        location = self.uploader.metadata_config.get('地点')
        wait_minute = self.uploader.metadata_config.get('视频超时报错', 10)

        page = await self.uploader.click_upload_video(page, wait_minute)
        page = await self.uploader.write_title(page, title)
        page = await self.uploader.write_describe(page, describe, labels)
        page = await self.uploader.set_location(page, location)
        page = await self.uploader.set_permission(page)
        page = await self.uploader.set_time(page)
        page = await self.uploader.click_publish(page)
        logger.info('视频发布成功, 3s自动返回')
        await page.wait_for_timeout(3000)
        return page


__all__ = ['XhsClient']
