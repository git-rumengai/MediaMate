import os
from abc import ABC, abstractmethod
import asyncio
import aiohttp
from functools import partial
from typing import Tuple, Optional, List
from mediamate.platforms.parser import XpathParser
from playwright.async_api import Page, Locator, BrowserContext

from mediamate.config import config, ConfigManager
from mediamate.tools.proxy import acheck_proxy
from mediamate.utils.schemas import MediaLoginInfo
from mediamate.utils.log_manager import log_manager
from mediamate.utils.const import OPEN_URL_TIMEOUT, DY_BASE_URL, DY_CREATOR_URL, XHS_BASE_URL, XHS_CREATOR_URL
from mediamate.utils.functions import get_useragent, get_direct_proxy, proxy_to_playwright

from mediamate.platforms.helpers import get_httpbin, check_cookies_valid, handle_dialog_accept
from mediamate.utils.enums import LocatorType, MediaType, PlatformType
from mediamate.tools.api_market.chat import Chat
from mediamate.platforms.helpers import message_reply, download_image
from mediamate.tools.converter.convert_to_hash import ConvertToHash
from mediamate.platforms.verify import RotateVerify, MoveVerify, BaseVerify



logger = log_manager.get_logger(__file__)


class BaseMedia(ABC):
    """  """
    def __init__(self):
        self.common_parser = XpathParser().init(f'{config.PROJECT_DIR}/platforms/static/elements/common.yaml')
        self.votate_verify = RotateVerify()
        self.move_verify = MoveVerify()

    async def verify_page(self, page: Page) -> Page:
        """  """
        if page.url.startswith(XHS_BASE_URL):
            verify = self.votate_verify
            slider_title = page.locator(self.common_parser.get_xpath('xhs_verify'))
            slider_bgimg = page.locator(self.common_parser.get_xpath('xhs_verify bg_img'))
            slider_gapimg = page.locator(self.common_parser.get_xpath('xhs_verify gap_img'))
            slider_bar = page.locator(self.common_parser.get_xpath('xhs_verify bar'))
        elif page.url.startswith(DY_BASE_URL):
            verify = self.move_verify
            slider_title = page.locator(self.common_parser.get_xpath('dy_verify'))
            slider_bgimg = page.locator(self.common_parser.get_xpath('dy_verify bg_img'))
            slider_gapimg = page.locator(self.common_parser.get_xpath('dy_verify gap_img'))
            slider_bar = page.locator(self.common_parser.get_xpath('dy_verify bar'))
        else:
            # logger.info(f'非主页: {page.url}')
            return page

        if await slider_title.is_visible():
            logger.info('出现滑块验证')
            for i in range(3):
                bg_url = await slider_bgimg.get_attribute('src')
                gap_url = await slider_gapimg.get_attribute('src')
                await self.move_slider(page, bg_url, gap_url, slider_bar, verify)
                if await slider_title.is_hidden():
                    break
                else:
                    logger.info(f'第 {i} 次尝试滑块验证失败')
                    if i == 3:
                        logger.info('请手动处理')
        return page

    async def move_slider(self, page: Page, bg_url: str, gap_url: str, slider: Locator, verify: BaseVerify) -> Page:
        """ 处理滑动框 """
        imgs_dir = os.path.abspath(f'{config.PROJECT_DIR}/platforms/static/imgs')
        # 下载图片
        prefix = page.url.split('.')[1]
        background_image_path = f'{imgs_dir}/{prefix}_bg.png'
        gap_image_path = f'{imgs_dir}/{prefix}_gap.png'
        result_image_path = f'{imgs_dir}/{prefix}_result.png'
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
            await page.mouse.move(x, y, steps=1)
            await page.wait_for_timeout(5)  # Simulate human-like sliding speed

        await page.mouse.up()

        # 等待一段时间以确保验证通过
        await page.wait_for_timeout(100)
        return page


class BaseClient(BaseMedia):
    def __init__(self):
        super().__init__()
        self.login_info = MediaLoginInfo()
        self.user_agent = get_useragent()
        self.base_url = ''
        self.creator_url = ''
        self.cookies_flag = ''
        self.browser_config = ConfigManager()
        self.convert_to_hash = ConvertToHash()
        self.uploader: BaseUploader = None
        self.chat = Chat()

    def init(self, info: MediaLoginInfo):
        self.login_info = info
        if self.login_info.platform == PlatformType.DY:
            self.base_url = DY_BASE_URL
            self.creator_url = DY_CREATOR_URL
            self.cookies_flag = '__security_server_data_status'
        elif self.login_info.platform == PlatformType.XHS:
            self.base_url = XHS_BASE_URL
            self.creator_url = XHS_CREATOR_URL
            self.cookies_flag = 'galaxy_creator_session_id'

        api_key = config.get('302__APIKEY')
        if api_key:
            self.chat.init(api_key)

    def get_reply_func(self, default: str, prompt: str) -> partial:
        """ 返回一个只需要传入messages的 reply 函数 """
        if config.get('302__APIKEY') and prompt:
            partial_reply = partial(message_reply, prompt=prompt, chat_api=self.chat)
        else:
            partial_reply = partial(message_reply, prompt=default)
        return partial_reply

    async def check_login_state(self, page: Optional[Page]) -> bool:
        """ 检查登录状态 """
        if not page:
            return False
        user_profile = ''
        if self.login_info.platform == PlatformType.DY:
            if page.url.startswith(DY_BASE_URL):
                user_profile = page.locator(self.common_parser.get_xpath('login dy_base'))
            elif page.url.startswith(DY_CREATOR_URL):
                user_profile = page.locator(self.common_parser.get_xpath('login dy_creator'))
        elif self.login_info.platform == PlatformType.XHS:
            if page.url.startswith(XHS_BASE_URL):
                user_profile = page.locator(self.common_parser.get_xpath('login xhs_base'))
            elif page.url.startswith(XHS_CREATOR_URL):
                user_profile = page.locator(self.common_parser.get_xpath('login xhs_creator'))
        if user_profile and await user_profile.is_visible():
            return True
        else:
            return False

    async def wait_login_state(self, page: Optional[Page]) -> bool:
        """ 检查登录状态 """
        if self.login_info.platform == PlatformType.DY:
            if page.url.startswith(DY_BASE_URL):
                user_profile = page.locator(self.common_parser.get_xpath('login dy_base'))
            else:
                user_profile = page.locator(self.common_parser.get_xpath('login dy_creator'))
        elif self.login_info.platform == PlatformType.XHS:
            if page.url.startswith(XHS_BASE_URL):
                user_profile = page.locator(self.common_parser.get_xpath('login xhs_base'))
            else:
                user_profile = page.locator(self.common_parser.get_xpath('login xhs_creator'))
        else:
            return False
        await user_profile.wait_for(timeout=OPEN_URL_TIMEOUT, state='visible')
        return True

    async def login(self, playwright, locator: LocatorType = LocatorType.HOME) -> Tuple[BrowserContext, Page]:
        """ 登录账户 """
        user_data_dir = f'{config.DATA_DIR}/browser/{self.login_info.platform.value}/{self.login_info.account}'
        os.makedirs(user_data_dir, exist_ok=True)

        # 将登陆的代理信息保存到本地
        temp_config_path = f'{user_data_dir}/config.yaml'
        self.browser_config.init(temp_config_path)
        temp_proxy = self.login_info.proxy if self.login_info.proxy else ''
        if temp_proxy == 'close':
            proxy = ''
        else:
            # 先使用账户配置中的代理
            if temp_proxy and await acheck_proxy(temp_proxy):
                proxy = temp_proxy
            else:
                # 再尝试历史保存的代码
                temp_proxy = self.browser_config.get('proxy') if self.browser_config.get('proxy') else ''
                if await acheck_proxy(temp_proxy):
                    proxy = temp_proxy
                else:
                    # 最后使用全局配置中的代理
                    proxy = await get_direct_proxy()
            await self.browser_config.set('proxy', proxy)
        logger.info(f'proxy: {proxy}')
        # 浏览器启动选项
        launch_options = {
            "user_data_dir": user_data_dir,
            "proxy": proxy_to_playwright(proxy),
            "bypass_csp": False,
            "args": [
                '--disable-blink-features=AutomationControlled',
            ]
        }

        # 无头模式和有头模式的上下文选项
        context_options_headless = {
            'channel': 'chrome',
            'headless': True,
            'permissions': ["geolocation"],
            'geolocation': {"longitude": self.login_info.location[0], "latitude": self.login_info.location[1]},
            'locale': 'zh-CN',
            'timezone_id': "Asia/Shanghai",
            'user_agent': self.user_agent
        }

        context_options_headed = {
            'channel': 'chrome',
            'headless': False,
            "viewport": {"width": 1920, "height": 1080},
            "slow_mo": 1000,
            'permissions': ["geolocation"],
            'geolocation': {"longitude": self.login_info.location[0], "latitude": self.login_info.location[1]},
            'locale': 'zh-CN',
            'timezone_id': "Asia/Shanghai",
            'user_agent': self.user_agent
        }

        # 1. 首先使用无头模式启动
        context = await playwright.chromium.launch_persistent_context(**launch_options, **context_options_headless)
        cookies = await context.cookies(self.base_url) if locator == LocatorType.HOME else await context.cookies(self.creator_url)
        if await check_cookies_valid(cookies, self.cookies_flag):
            logger.info('cookies有效, 直接登录')
            if not self.login_info.headless:
                logger.info('设置有头模式, 重新打开页面')
                # headless有头, 需要重新打来浏览器
                await context.close()
                context = await playwright.chromium.launch_persistent_context(**launch_options, **context_options_headed)
        else:
            logger.info('cookies无效, 打开页面登录')
            # 关闭浏览器重新以有头模式打开
            await context.close()
            context = await playwright.chromium.launch_persistent_context(**launch_options, **context_options_headed)

        # 开启跟踪模式
        await context.tracing.start(screenshots=True, snapshots=True)
        page = context.pages[0]
        # 浏览器检测工具
        # await page.goto('https://abrahamjuliot.github.io/creepjs/')

        # 注册弹窗处理程序, 必须要在打开页面之前
        page.on('dialog', handle_dialog_accept)
        logger.info(f'user_agent: {self.user_agent}')
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

        if locator == LocatorType.HOME:
            await page.goto(self.base_url, timeout=OPEN_URL_TIMEOUT)
        else:
            await page.goto(self.creator_url, timeout=OPEN_URL_TIMEOUT)
        await page.wait_for_load_state('load')
        await self.verify_page(page)
        if await self.check_login_state(page):
            logger.info(f'用户保持登录: {self.login_info.account}')
        else:
            logger.info(f'用户未登录: {self.login_info.account}, 请在{OPEN_URL_TIMEOUT / 1000}内登录...')
            try:
                await self.wait_login_state(page)
                logger.info(f'用户登录成功')
            except Exception as e:
                logger.info('用户登录失败')
        return context, page

    @abstractmethod
    async def upload_text(self, page: Page) -> Optional[Page]:
        """  """

    @abstractmethod
    async def upload_video(self, page: Page) -> Optional[Page]:
        """  """

    async def start_upload(self, page: Page):
        """  """
        data_dir = f'{config.DATA_DIR}/upload/{self.login_info.platform.value}/{self.login_info.account}'
        for path in os.listdir(data_dir):
            full_path = os.path.join(data_dir, path)
            if os.path.isdir(full_path):
                self.uploader.upload_data_dir = full_path
                logger.info(f'发表文件路径: {full_path}')
                media_type, files = self.uploader.check_upload_type()
                saved_files = self.browser_config.get('published', [])
                hash_files = self.convert_to_hash.process_input(files)
                if any(hash_file in saved_files for hash_file in hash_files):
                    logger.info(f'存在已发布过的文件')
                    continue
                else:
                    saved_files.extend(hash_files)
                if media_type.value == MediaType.IMAGE.value:
                    logger.info('检测到发表图文内容')
                    page = await self.upload_text(page)
                    await self.browser_config.set('published', saved_files)  # 更新配置
                elif media_type.value == MediaType.VIDEO.value:
                    logger.info('检测到发表视频内容')
                    page = await self.upload_video(page)
                    await self.browser_config.set('published', saved_files)  # 更新配置
                else:
                    logger.info('未检测到任何可发表内容')
        return page


class BaseLocator(BaseMedia):
    def __init__(self):
        super().__init__()
        self.parser = XpathParser()

    def init(self, elements_path):
        """  """
        self.parser.init(elements_path)
        return self

    async def scroll(self, page: Page):
        """ 滚动页面 """
        await page.evaluate("window.scrollBy(0, window.innerHeight)")

    async def ensure_page(self, page) -> Page:
        """ 处理页面加载异常, 只能使用"self.parser.get_xpath" """

    async def get_locator(self, page: Page, parser_path: str, index: int=0) -> Locator:
        """
        以"_"开头是xpath的子节点
        以"_list"结尾是xpath列表
        其他则为一般xpath节点
        """
        await self.verify_page(page)
        await self.ensure_page(page)
        xpath = self.parser.get_xpath(parser_path)
        if index:
            xpath=f'{xpath}[{index}]'
        locator = page.locator(xpath)
        return locator

    async def get_child_locator(self, parent: Locator, child_path: str, index: int=0) -> Locator:
        """ 通过父节点locator定位到子节点 """
        xpath = f'xpath={self.parser.get_xpath(child_path)}'
        if index:
            xpath = f'{xpath}[{index}]'
        locator = parent.locator(xpath)
        return locator

    async def get_visible_locator(self, page: Page, parser_path: str) -> Locator:
        """  """
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=OPEN_URL_TIMEOUT, state='visible')
        return locator

    async def get_child_visible_locator(self, parent: Locator, child_path: str) -> Locator:
        """ 通过父类locator定位到子类 """
        locator = await self.get_child_locator(parent, child_path)
        await locator.wait_for(timeout=OPEN_URL_TIMEOUT, state='visible')
        return locator

    async def get_visible_locators(self, page: Page, parser_path: str) -> Locator:
        """ 传入的是列表的父类, 一定要是唯一的 """
        locator1 = await self.get_locator(page, parser_path, 1)
        await locator1.wait_for(timeout=OPEN_URL_TIMEOUT, state='visible')
        locator = await self.get_locator(page, parser_path)
        return locator

    async def get_child_visible_locators(self, parent: Locator, child_path: str) -> Locator:
        """ 通过父类locator定位到子类 """
        locator1 = await self.get_child_locator(parent, child_path, 1)
        await locator1.wait_for(timeout=OPEN_URL_TIMEOUT, state='visible')
        locator = await self.get_child_locator(parent, child_path)
        return locator

    async def get_hidden_locator(self, page: Page, parser_path: str) -> Locator:
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')
        return locator

    async def get_attached_locator(self, page: Page, parser_path: str) -> Locator:
        """  """
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=OPEN_URL_TIMEOUT, state='attached')
        return locator

    async def get_detached_locator(self, page: Page, parser_path: str) -> Locator:
        """  """
        locator = await self.get_locator(page, parser_path)
        await locator.wait_for(timeout=OPEN_URL_TIMEOUT, state='detached')
        return locator

    async def ensure_step_page(self, page: Page, steps: Tuple[str, ...] = ()):
        """ 确保页面没有重新加载 """
        await self.ensure_page(page)
        for step in steps:
            step_locator = await self.get_visible_locator(page, step)
            await step_locator.wait_for(timeout=OPEN_URL_TIMEOUT, state='visible')
            await step_locator.click()
            await self.ensure_page(page)


class BaseUploader(BaseLocator):
    @abstractmethod
    def check_upload_type(self) -> Tuple[MediaType, List[str]]:
        """ 检查上传文件类型类型 """
