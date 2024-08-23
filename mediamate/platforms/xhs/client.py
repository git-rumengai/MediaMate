from typing import Optional

from playwright.async_api import Page, async_playwright, Playwright

from mediamate.utils.log_manager import log_manager
from mediamate.platforms.xhs.uploader import XhsUploader
from mediamate.platforms.xhs.downloader import XhsDownloader
from mediamate.platforms.xhs.channel import XhsChannel
from mediamate.platforms.xhs.operator import XhsOperator
from mediamate.platforms.base import BaseClient
from mediamate.utils.schemas import MediaInfo


logger = log_manager.get_logger(__file__)


class XhsClient(BaseClient):
    def __init__(self, info: MediaInfo):
        super().__init__(info)
        self.uploader = XhsUploader(info)
        self.downloader = XhsDownloader(info)
        self.channel = XhsChannel(info)
        self.operator = XhsOperator(info)

    async def start_home(self, playwright: Optional[Playwright] = None):
        """ home页面可以进行的操作 """
        async def _start(playwright):
            context, page = await self.login(playwright)
            try:
                page = await self._public_explore(page)
                await self.wait_long(page)
                page = await self._public_download(page)
                await self.wait_long(page)
                page = await self._public_comment(page)
                await self.wait_long(page)
                page = await self._private_operator(page)
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
        """ creator页面可以进行的操作 """
        async def _start(playwright):
            context, page = await self.login(playwright)
            try:
                if self.account_info.creator.get('upload'):
                    page = await self.uploader.start_upload(page)
                    await self.wait_long(page)
                await self.wait_long(page)
                page = await self._private_download(page)
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

    async def _public_explore(self, page: Page) -> Page:
        """ 浏览首页 """
        explore = self.account_info.home.get('explore')
        if explore:
            topics = explore.get('topics', ())
            times = explore.get('times', 1)
            actions = explore.get('actions', ())
            mention = explore.get('mention', ())
            page = await self.channel.channel_explore(page, topics=topics, times=times, actions=actions, mention=mention)
        return page

    async def _public_comment(self, page: Page) -> Page:
        """  """
        comment = self.account_info.home.get('comment')
        if comment:
            ids = comment.get('ids', ())
            times = comment.get('times', 1)
            actions = comment.get('actions', ())
            mention = comment.get('mention', ())
            shuffle = comment.get('shuffle', False)
            page = await self.channel.channel_comment(page, ids=ids, times=times, actions=actions, mention=mention, shuffle=shuffle)
        return page

    async def _private_operator(self, page: Page) -> Page:
        """ 从home页回复自己作品的评论 """
        operator = self.account_info.home.get('operate')
        if operator and operator.get('comment'):
            page = await self.operator.click_comment(page)
        return page

    async def _public_download(self, page: Page) -> Page:
        """  """
        download = self.account_info.home.get('download')
        if download:
            ids = download.get('ids', ())
            page = await self.channel.channel_download(page, ids=ids)
        return page

    async def _private_download(self, page: Page) -> Page:
        """  """
        download = self.account_info.creator.get('download')
        if download:
            page = await self.downloader.click_creator(page)
            page = await self.downloader.click_inspiration(page, topics=tuple(download))
        return page


__all__ = ['XhsClient']
