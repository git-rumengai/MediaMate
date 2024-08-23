import os
from abc import ABC, abstractmethod
import asyncio
import aiohttp
from typing import Tuple, Optional, List, Callable, Dict, Awaitable
from mediamate.platforms.parser import XpathParser
from playwright.async_api import Page, Locator, BrowserContext

from mediamate.config import ConfigManager
from mediamate.tools.proxy import acheck_proxy
from mediamate.utils.schemas import MediaInfo, MediaPath
from mediamate.utils.log_manager import log_manager
from mediamate.utils.const import (
    DEFAULT_LOCATION,
    DEFAULT_URL_TIMEOUT,
    TRACE_PLAYWRIGHT_DEV,
    DEFAULT_COMMENT,
    DEFAULT_REPLY_COMMENT,
    DEFAULT_CHAT,
    DEFAULT_REPLY_CHAT,
    DEFAULT_VIDEO_WAIT,
    DEFAULT_IMAGE_WAIT,
    DEFAULT_DATA_LENGTH,
    DEFAULT_REPLY_COMMENT_LENGTH,
    DEFAULT_REPLY_COMMENT_DAYS,
    DEFAULT_REPLY_COMMENT_TIMES,
    DEFAULT_REPLY_CHAT_LENGTH
)
from mediamate.utils.functions import get_useragent, get_direct_proxy, proxy_to_playwright

from mediamate.platforms.helpers import get_httpbin, handle_dialog_accept, download_image
from mediamate.utils.enums import MediaType, UrlType
from mediamate.tools.converter.convert_to_hash import ConvertToHash
from mediamate.platforms.verify import RotateVerify, MoveVerify, BaseVerify


logger = log_manager.get_logger(__file__)
# 定义一个异步的 Callable 类型
AsyncCallable = Callable[..., Awaitable[str | bool]]

"""
setTimeout(function() {
    debugger;
}, 3000);
"""


class BaseMedia(ABC):
    """  """
    def __init__(self, info: MediaInfo):
        self.account_info = info
        self.data_path: Optional[MediaPath] = MediaPath(info=info)
        self.parser_common = XpathParser(self.data_path.elements_common_file)
        self.parser = XpathParser(self.data_path.elements_home_file) if info.subdomain == 'www' else XpathParser(self.data_path.elements_creator_file)
        self.active_config = ConfigManager(self.data_path.active_config_file)

        # 破解验证码
        self.votate_verify = RotateVerify()
        self.move_verify = MoveVerify()

    async def verify_page(self, page: Page) -> Page:
        """  """
        if self.account_info.domain == 'xiaohongshu':
            verify = self.votate_verify
            slider_title = page.locator(self.parser_common.get_xpath('xhs_verify'))
            slider_bgimg = page.locator(self.parser_common.get_xpath('xhs_verify bg_img'))
            slider_gapimg = page.locator(self.parser_common.get_xpath('xhs_verify gap_img'))
            slider_bar = page.locator(self.parser_common.get_xpath('xhs_verify bar'))
        elif self.account_info.domain == 'douyin':
            verify = self.move_verify
            slider_title = page.locator(self.parser_common.get_xpath('dy_verify'))
            slider_bgimg = page.locator(self.parser_common.get_xpath('dy_verify bg_img'))
            slider_gapimg = page.locator(self.parser_common.get_xpath('dy_verify gap_img'))
            slider_bar = page.locator(self.parser_common.get_xpath('dy_verify bar'))
        else:
            logger.info(f'未知域名: {self.account_info.domain}')
            return page

        if await slider_title.count() > 0:
            # 抖音的无法判断? is_visible
            logger.info('出现滑块验证')
            for i in range(3):
                bg_url = await slider_bgimg.get_attribute('src')
                gap_url = await slider_gapimg.get_attribute('src')
                await self.move_slider(page, bg_url, gap_url, slider_bar, verify)
                await self.wait_long(page, 3)
                if await slider_title.is_hidden():
                    break
                else:
                    logger.info(f'第 {i} 次尝试滑块验证失败')
                    if i == 3:
                        logger.info('请手动处理')
        return page

    async def move_slider(self, page: Page, bg_url: str, gap_url: str, slider: Locator, verify: BaseVerify) -> Page:
        """ 处理滑动框 """
        # 下载图片
        prefix = page.url.split('.')[1]
        background_image_path = f'{self.data_path.static_imgs}/{prefix}_bg.png'
        gap_image_path = f'{self.data_path.static_imgs}/{prefix}_gap.png'
        result_image_path = f'{self.data_path.static_imgs}/{prefix}_result.png'
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                download_image(session, bg_url, background_image_path),
                download_image(session, gap_url, gap_image_path)
            )

        distance = verify.calculate(background_image_path, gap_image_path, result_image_path)
        path = await verify.calculate_path(slider, distance)
        await slider.scroll_into_view_if_needed()
        await slider.hover()
        await page.mouse.down()

        for point in path:
            x, y = point
            await page.mouse.move(x, y, steps=10)
            await self.wait_short(page)

        await page.mouse.up()
        # 等待一段时间以确保验证通过
        await self.wait_short(page)
        return page

    async def wait_short(self, page: Page):
        """ 等待100ms """
        await page.wait_for_timeout(100)

    async def wait_medium(self, page: Page):
        """ 等待100ms """
        await page.wait_for_timeout(300)

    async def wait_long(self, page: Page, seconds: int = 1):
        """ 等待1s """
        await page.wait_for_timeout(1000 * seconds)


class BaseClient(BaseMedia):
    async def wait_login_state(self, page: Optional[Page]) -> bool:
        """ 等待登录完毕 """
        if self.account_info.url == UrlType.DY_HOME_URL:
            user_profile = page.locator(self.parser_common.get_xpath('login dy_home'))
        elif self.account_info.url == UrlType.DY_CREATOR_URL:
            user_profile = page.locator(self.parser_common.get_xpath('login dy_creator'))
        elif self.account_info.url == UrlType.XHS_HOME_URL:
            user_profile = page.locator(self.parser_common.get_xpath('login xhs_home'))
        elif self.account_info.url == UrlType.XHS_CREATOR_URL:
            user_profile = page.locator(self.parser_common.get_xpath('login xhs_creator'))
        else:
            raise ValueError(f'未知的url地址: {self.account_info.url}')
        if user_profile and await user_profile.is_visible():
            return True
        else:
            logger.info('等待登录中...')
            await user_profile.wait_for(timeout=DEFAULT_URL_TIMEOUT * 3, state='visible')
        return True

    async def login(self, playwright) -> Tuple[BrowserContext, Page]:
        """ 登录账户 """
        # 将登陆的代理信息保存到本地
        temp_proxy = self.account_info.proxy if self.account_info.proxy else ''
        if temp_proxy == 'close':
            proxy = ''
        else:
            # 先使用账户配置中的代理
            if temp_proxy and await acheck_proxy(temp_proxy):
                proxy = temp_proxy
            else:
                # 再尝试历史保存的代码
                temp_proxy = self.active_config.get('proxy') if self.active_config.get('proxy') else ''
                if await acheck_proxy(temp_proxy):
                    proxy = temp_proxy
                else:
                    # 最后使用全局配置中的代理
                    proxy = await get_direct_proxy()
            await self.active_config.set('proxy', proxy)
        logger.info(f'proxy: {proxy}')
        user_data_dir = self.data_path.browser_home if self.account_info.subdomain == 'www' else self.data_path.browser_creator
        # 浏览器启动选项
        launch_options = {
            "user_data_dir": user_data_dir,
            "proxy": proxy_to_playwright(proxy),
            "bypass_csp": False,
            "args": [
                '--disable-blink-features=AutomationControlled',
            ]
        }

        user_agent = get_useragent()
        # 无头模式和有头模式的上下文选项
        context_options_headless = {
            'channel': 'chrome',
            'headless': True,
            'permissions': ["geolocation"],
            'geolocation': {"longitude": DEFAULT_LOCATION[0], "latitude": DEFAULT_LOCATION[1]},
            'locale': 'zh-CN',
            'timezone_id': "Asia/Shanghai",
            'user_agent': user_agent
        }

        context_options_headed = {
            'channel': 'chrome',
            'headless': False,
            "viewport": {"width": 1920, "height": 1080},
            "slow_mo": 1000,
            'permissions': ["geolocation"],
            'geolocation': {"longitude": DEFAULT_LOCATION[0], "latitude": DEFAULT_LOCATION[1]},
            'locale': 'zh-CN',
            'timezone_id': "Asia/Shanghai",
            'user_agent': user_agent
        }

        if self.account_info.headless:
            logger.info('无头模式启动')
            context = await playwright.chromium.launch_persistent_context(**launch_options, **context_options_headless)
        else:
            logger.info('有头模式启动')
            context = await playwright.chromium.launch_persistent_context(**launch_options, **context_options_headed)

        # 开启跟踪模式
        await context.tracing.start(screenshots=True, snapshots=True)
        page = context.pages[0]
        # 浏览器检测工具
        # await page.goto('https://abrahamjuliot.github.io/creepjs/')

        # 注册弹窗处理程序, 必须要在打开页面之前
        page.on('dialog', handle_dialog_accept)
        if proxy:
            httpbin = await get_httpbin(proxy)
            logger.info(f'代理ip: {httpbin}')
            url = f'http://ip-api.com/json/{httpbin.strip()}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"国家: {data['country']}, 省/州: {data['regionName']}, 城市: {data['city']}")
                        logger.info(f"经纬度: {data['lat']}, {data['lon']}")  # 经纬度
                    else:
                        logger.info('ip信息检测失败, 忽略')

        await page.goto(self.account_info.url.value, timeout=DEFAULT_URL_TIMEOUT)
        await page.wait_for_load_state('load')
        await self.verify_page(page)
        await self.wait_login_state(page)
        return context, page

    async def close_context(self, context: BrowserContext, filename: str):
        # 停止跟踪并保存文件
        trace_file = os.path.join(self.data_path.active, filename)
        await context.tracing.stop(path=trace_file)
        await context.close()
        logger.info(f'可进入查看跟踪结果: {TRACE_PLAYWRIGHT_DEV} , file: {filename}')


class BaseLocator(BaseMedia):
    def __init__(self, info: MediaInfo):
        super().__init__(info)
        self.convert_to_hash = ConvertToHash()

        # 默认配置
        self.default_comment_message = self.account_info.common.get('default_comment_message', DEFAULT_COMMENT)
        self.default_comment_reply_message = self.account_info.common.get('default_comment_reply_message', DEFAULT_REPLY_COMMENT)
        self.default_chat_message = self.account_info.common.get('default_chat_message', DEFAULT_CHAT)
        self.default_chat_reply_message = self.account_info.common.get('default_chat_reply_message', DEFAULT_REPLY_CHAT)

        self.default_data_length = self.account_info.common.get('default_data_length', DEFAULT_DATA_LENGTH)
        self.default_reply_chat_length = self.account_info.common.get('default_reply_chat_length', DEFAULT_REPLY_CHAT_LENGTH)
        self.default_reply_comment_length = self.account_info.common.get('default_reply_comment_length', DEFAULT_REPLY_COMMENT_LENGTH)
        self.default_reply_comment_days = self.account_info.common.get('default_reply_comment_days', DEFAULT_REPLY_COMMENT_DAYS)
        self.default_reply_comment_times = self.account_info.common.get('default_reply_comment_times', DEFAULT_REPLY_COMMENT_TIMES)
        self.default_image_wait = self.account_info.common.get('default_video_wait', DEFAULT_VIDEO_WAIT)
        self.default_video_wait = self.account_info.common.get('default_image_wait', DEFAULT_IMAGE_WAIT)

        # AI处理
        self.ai_content_filter: Optional[AsyncCallable] = None
        self.ai_user_filter: Optional[AsyncCallable] = None
        self.ai_content_comment: Optional[AsyncCallable] = None
        self.ai_content_comment_reply: Optional[AsyncCallable] = None
        self.ai_content_chat: Optional[AsyncCallable] = None
        self.ai_content_chat_reply: Optional[AsyncCallable] = None

    async def scroll(self, page: Page):
        """ 直接滚动页面 """
        await page.evaluate("window.scrollBy(0, window.innerHeight)")

    async def wheel(self, page: Page, delta_x: int = 0, delta_y: int = 500):
        """ 模拟滑轮滚动 """
        await page.mouse.wheel(delta_x, delta_y)

    async def ensure_page(self, page) -> Page:
        """ 处理页面加载异常, 只能使用"self.parser.get_xpath" """
        raise NotImplementedError('没有处理可能出现的页面异常')

    async def get_locator(self, page: Page, parser_path: str) -> Locator:
        """
        以"_"开头是xpath的子节点
        以"_list"结尾是xpath列表
        其他则为一般 xpath 节点
        """
        await self.verify_page(page)
        await self.ensure_page(page)
        xpath = self.parser.get_xpath(parser_path)
        locator = page.locator(xpath)
        return locator

    async def get_child_locator(self, parent: Locator, child_path: str) -> Locator:
        """ 通过父节点locator定位到子节点 """
        xpath = f'xpath={self.parser.get_xpath(child_path)}'
        locator = parent.locator(xpath)
        return locator

    async def get_visible_locator(self, page: Page, parser_path: str) -> Locator:
        """  """
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='visible')
        return locator

    async def get_child_visible_locator(self, parent: Locator, child_path: str) -> Locator:
        """ 通过父类locator定位到子类 """
        locator = await self.get_child_locator(parent, child_path)
        await locator.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='visible')
        return locator

    async def get_visible_locators(self, page: Page, parser_path: str) -> Locator:
        """ 传入的是列表的父类, 一定要是唯一的 """
        locator = await self.get_locator(page, parser_path)
        await locator.first.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='visible')
        return locator

    async def get_child_visible_locators(self, parent: Locator, child_path: str) -> Locator:
        """ 通过父类locator定位到子类 """
        locator = await self.get_child_locator(parent, child_path)
        await locator.first.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='visible')
        return locator

    async def get_hidden_locator(self, page: Page, parser_path: str) -> Locator:
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='hidden')
        return locator

    async def get_attached_locator(self, page: Page, parser_path: str) -> Locator:
        """  """
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='attached')
        return locator

    async def get_detached_locator(self, page: Page, parser_path: str) -> Locator:
        """  """
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='detached')
        return locator

    async def ensure_step_page(self, page: Page, steps: Tuple[str, ...] = ()):
        """ 确保页面没有重新加载 """
        await self.ensure_page(page)
        for step in steps:
            step_locator = await self.get_visible_locator(page, step)
            await step_locator.wait_for(timeout=DEFAULT_URL_TIMEOUT, state='visible')
            await step_locator.click()
            await self.ensure_page(page)

    async def wait_first_locator(self, locators: list[Locator]) -> int:
        """ 在给定的 locators 列表中，等待第一个出现的 locator，并返回该 locator 在列表中的索引位置。 """
        tasks = [
            asyncio.create_task(locator.wait_for(state='visible', timeout=DEFAULT_URL_TIMEOUT))
            for locator in locators
        ]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # 找到第一个成功完成的任务的索引
        for i, task in enumerate(tasks):
            if task in done and not task.cancelled() and task.exception() is None:
                # 取消所有未完成的任务
                for p in pending:
                    p.cancel()
                return i

        raise TimeoutError('Locator 等待超时')

    def register_content_filter(self, callback: AsyncCallable):
        """ 添加ai功能 """
        self.ai_content_filter = callback

    async def media_content_filter(self, content: List[Dict[str, str]]) -> bool:
        """ 内容过滤: True保留, False过滤 """
        result = True
        if self.ai_content_filter:
            response = await self.ai_content_filter(content)
            result = False if 'false' in response.lower() else True
        return result

    def register_user_filter(self, callback: AsyncCallable):
        """ 添加ai功能 """
        self.ai_user_filter = callback

    async def media_user_filter(self, content: List[Dict[str, str]]) -> bool:
        """ 通过用户评论决定是否私聊: True保留, False过滤 """
        result = True
        if self.ai_user_filter:
            response = await self.ai_user_filter(content)
            result = False if 'false' in response.lower() else True
        return result

    def register_content_comment(self, callback: AsyncCallable):
        """ 添加ai功能 """
        self.ai_content_comment = callback

    async def media_content_comment(self, content: List[Dict[str, str]]) -> str:
        """ 评论 """
        result = self.default_comment_message
        if self.ai_content_comment:
            result = await self.ai_content_comment(content)
        return result

    def register_content_comment_reply(self, callback: AsyncCallable):
        """ 添加ai功能 """
        self.ai_content_comment_reply = callback

    async def media_content_comment_reply(self, content: List[Dict[str, str]]) -> str:
        """ 回复评论 """
        result = self.default_comment_reply_message
        if self.ai_content_comment_reply:
            result = await self.ai_content_comment_reply(content)
        return result

    def register_content_chat(self, callback: AsyncCallable):
        """ 添加ai功能 """
        self.ai_content_chat = callback

    async def media_content_chat(self, content: List[Dict[str, str]]) -> str:
        """ 主动私聊 """
        result = self.default_chat_message
        if self.ai_content_chat:
            result = await self.ai_content_chat(content)
        return result

    def register_content_chat_reply(self, callback: AsyncCallable):
        """ 添加ai功能 """
        self.ai_content_chat_reply = callback

    async def media_content_chat_reply(self, content: List[Dict[str, str]]) -> str:
        """ 回复私聊 """
        result = self.default_chat_reply_message
        if self.ai_content_chat_reply:
            result = await self.ai_content_chat_reply(content)
        return result


class BaseUploader(BaseLocator):
    @abstractmethod
    def check_upload_type(self, data_dir: str) -> Tuple[MediaType, List[str]]:
        """ 检查上传文件类型类型 """
        pass

    @abstractmethod
    async def upload_text(self, page: Page, data_dir: str) -> Optional[Page]:
        """  """

    @abstractmethod
    async def upload_video(self, page: Page, data_dir: str) -> Optional[Page]:
        """  """

    async def start_upload(self, page: Page):
        """  """
        for path in os.listdir(self.data_path.upload):
            full_path = os.path.join(self.data_path.upload, path)
            if os.path.isdir(full_path):
                logger.info(f'发表文件路径: {full_path}')
                media_type, files = self.check_upload_type(full_path)
                saved_files = self.active_config.get('published', [])
                hash_files = self.convert_to_hash.process_input(files)
                if any(hash_file in saved_files for hash_file in hash_files):
                    logger.info(f'存在已发布过的文件')
                    continue
                else:
                    saved_files.extend(hash_files)
                if media_type.value == MediaType.IMAGE.value:
                    logger.info('检测到发表图文内容')
                    page = await self.upload_text(page, full_path)
                    await self.active_config.set('published', saved_files)  # 更新配置
                elif media_type.value == MediaType.VIDEO.value:
                    logger.info('检测到发表视频内容')
                    page = await self.upload_video(page, full_path)
                    await self.active_config.set('published', saved_files)  # 更新配置
                else:
                    logger.info('未检测到任何可发表内容')
        return page
