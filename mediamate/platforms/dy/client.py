from typing import Optional
from playwright.async_api import Page, async_playwright, Playwright

from mediamate.utils.schema import MediaInfo
from mediamate.utils.log_manager import log_manager
from mediamate.platforms.dy.upload import DyUploader
from mediamate.platforms.dy.download import DyDownloader
from mediamate.platforms.dy.operate import DyOperator
from mediamate.platforms.dy.channel import DyChannel
from mediamate.platforms.base import BaseClient


logger = log_manager.get_logger(__file__)


class DyClient(BaseClient):
    def __init__(self, info: MediaInfo):
        super().__init__(info)
        self.channel = DyChannel(info)
        self.uploader = DyUploader(info)
        self.downloader = DyDownloader(info)
        self.operator = DyOperator(info)

    async def start_home(self, playwright: Optional[Playwright] = None):
        """启动基础流程，支持内部与外部 Playwright 上下文管理器"""
        async def _start(playwright):
            context, page = await self.login(playwright)
            try:
                page = await self._public_discover(page)
                await self.wait_long(page)
                page = await self._public_download(page)
                await self.wait_long(page)
                page = await self._public_comment(page)
                await self.wait_long(page)
                page = await self._public_follow(page)
                await self.wait_long(page)
                # 回复私信放最后(因为私信加载最慢)
                await self._private_operate(page)
                await self.wait_long(page)
            except Exception as e:
                logger.error(e)
            finally:
                await self.close_context(context, 'trace_home.zip')

        if playwright:
            await _start(playwright)
        else:
            async with async_playwright() as playwright:
                await _start(playwright)

    async def start_creator(self, playwright: Optional[Playwright] = None):
        """启动基础流程，支持内部与外部 Playwright 上下文管理器"""
        async def _start(playwright):
            context, page = await self.login(playwright)
            try:
                if self.account_info.creator.get('upload'):
                    await self.uploader.start_upload(page)
                    await self.wait_long(page)
                await self._private_download(page)
                await self.wait_long(page)
            except Exception as e:
                logger.error(e)
            finally:
                await self.close_context(context, 'trace_creator.zip')

        if playwright:
            await _start(playwright)
        else:
            async with async_playwright() as playwright:
                await _start(playwright)

    async def _private_download(self, page: Page):
        """ 下载私人数据 """
        downloader = self.account_info.creator.get('download')
        if downloader:
            if downloader.get('manage'):
                page = await self.downloader.click_manage(page)
            if downloader.get('datacenter'):
                page = await self.downloader.click_datacenter(page)
            if downloader.get('creative_guidance'):
                page = await self.downloader.click_creative_guidance(page, tuple(downloader.get('creative_guidance')))
            if downloader.get('billboard'):
                page = await self.downloader.click_billboard(page, tuple(downloader.get('billboard')))
        return page

    async def _private_operate(self, page: Page):
        """ 回复私人评论或私信 """
        operator = self.account_info.home.get('operate')
        if operator:
            comment = operator.get('comment')
            chat = operator.get('chat')
            if comment:
                page = await self.operator.click_comment(page)
            if chat:
                page = await self.operator.click_chat(page)
        return page

    async def _public_discover(self, page: Page) -> Page:
        """ 随机浏览首页信息 """
        discover = self.account_info.home.get('discover')
        if discover:
            topics = discover.get('topics', ())
            times = discover.get('times', 1)
            actions = discover.get('actions', ())
            mention = discover.get('mention', ())
            page = await self.channel.channel_discover(page, topics=topics, times=times, actions=actions, mention=mention)
        return page

    async def _public_download(self, page: Page) -> Page:
        """ 下载指定用户的视频信息 """
        download = self.account_info.home.get('download')
        if download:
            ids = download.get('ids', ())
            page = await self.channel.channel_download(page, ids=ids)
        return page

    async def _public_comment(self, page: Page) -> Page:
        """ 评论指定用户的视频 """
        comment = self.account_info.home.get('comment')
        if comment:
            ids = comment.get('ids', ())
            times = comment.get('times', 1)
            actions = comment.get('actions', ())
            mention = comment.get('mention', ())
            shuffle = comment.get('shuffle', False)
            page = await self.channel.channel_comment(page, ids=ids, times=times, actions=actions, mention=mention, shuffle=shuffle)
        return page

    async def _public_follow(self, page: Page) -> Page:
        """ 从指定用户的评论区添加好友 """
        follow = self.account_info.home.get('follow')
        if follow:
            ids = follow.get('ids', ())
            times = follow.get('times', 1)
            batch = follow.get('batch', 1)
            shuffle = follow.get('shuffle', False)
            page = await self.channel.channel_target(page, ids=ids, times=times, batch=batch, shuffle=shuffle)
        return page


__all__ = ['DyClient']
