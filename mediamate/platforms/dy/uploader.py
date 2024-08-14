import os
import re
import glob
from typing import Optional, Tuple, List
from playwright.async_api import Page

from mediamate.utils.const import OPEN_URL_TIMEOUT
from mediamate.utils.log_manager import log_manager
from mediamate.utils.schemas import MediaLoginInfo
from mediamate.config import config, ConfigManager
from mediamate.utils.enums import MediaType
from mediamate.platforms.base import BaseUploader


logger = log_manager.get_logger(__file__)


class DyUploader(BaseUploader):
    """ 发布页操作 """
    VIDEO_EXTENSIONS = ['*.mp4', '*.m4v', '*.avi', '*.mov', '*.webm', '*.flv', '*.mkv']
    IMAGE_EXTENSIONS = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif',  '*.webp']

    def __init__(self):
        super().__init__()
        self.upload_data_dir: str = ''
        self.metadata_config: ConfigManager = ConfigManager()

    def init(self, info: MediaLoginInfo):
        """ 抖音默认以发视频为主 """
        elements_path = f'{config.PROJECT_DIR}/platforms/static/elements/dy/creator.yaml'
        super().init(elements_path)

        self.upload_data_dir = f'{config.DATA_DIR}/upload/douyin/{info.account}'
        os.makedirs(self.upload_data_dir, exist_ok=True)
        return self

    def check_upload_type(self) -> Tuple[MediaType, List[str]]:
        """ 检查上传作品类型, 视频优先 """
        self.metadata_config.init(f'{self.upload_data_dir}/metadata.yaml')
        title = self.metadata_config.get('标题')
        describe = self.metadata_config.get('描述')
        if not (title and describe):
            raise ValueError(f'发表信息数据不完整, : {self.upload_data_dir}')

        video_files = []
        for extension in self.VIDEO_EXTENSIONS:
            video_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))
        if video_files:
            return MediaType.VIDEO, video_files
        else:
            image_files = []
            for extension in self.IMAGE_EXTENSIONS:
                image_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))
            if image_files:
                return MediaType.IMAGE, image_files
            else:
                raise ValueError(f'没有视频和图片文件, 无法发布: {self.upload_data_dir}')

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

    async def click_note(self, page: Page) -> Optional[Page]:
        """  """
        logger.info('点击发布作品')
        steps = ('home', 'home text_datacenter', 'upload', 'upload video')
        await self.ensure_step_page(page, steps)

        tips_youknow = page.locator(self.parser.get_xpath('common tips_youknow'))
        if await tips_youknow.is_visible():
            await tips_youknow.click()
        return page

    async def click_upload_video(self, page: Page, wait_minute: int = 10) -> Optional[Page]:
        """  """
        logger.info('点击发布视频')
        steps = ('upload video', )
        await self.ensure_step_page(page, steps)

        video_files = []
        for extension in DyUploader.VIDEO_EXTENSIONS:
            video_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))

        # 如果没有视频文件，返回空列表
        if video_files:
            # 获取每个视频文件的大小并排序
            video_files_with_size = [(file, os.path.getsize(file)) for file in video_files]
            video_files_with_size.sort(key=lambda x: x[1])
            file = video_files_with_size[0][0]
            if len(video_files) > 1:
                logger.warning(f'视频文件超过一个, 默认选择最小的视频文件上传: {file}')

            input_video = page.locator(self.parser.get_xpath('upload video_input'))
            await input_video.wait_for(timeout=OPEN_URL_TIMEOUT, state='attached')
            await input_video.set_input_files(file)

            logger.info(f'准备上传: {file}')
            cancel_video = await self.get_locator(page, 'upload video_cancel')
            await cancel_video.wait_for(timeout=OPEN_URL_TIMEOUT * 3, state='visible')
            logger.info(f'视频上传中...')
            await cancel_video.wait_for(timeout=OPEN_URL_TIMEOUT * wait_minute, state='hidden')
            logger.info(f'文件上传成功: {file}')
            return page

    async def click_upload_image(self, page: Page, wait_minute: int = 3) -> Optional[Page]:
        """  """
        logger.info('点击发布图文')
        steps = ('upload image', )
        await self.ensure_step_page(page, steps)

        image_files = []
        for extension in DyUploader.IMAGE_EXTENSIONS:
            image_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))
        # 如果没有文件，返回空列表. dy最多上传35张图片
        if image_files:
            if len(image_files) > 35:
                logger.warning(f'图片文件数量超过35, 只上传35张图片')

            file = image_files[0]
            input_image = await self.get_locator(page, 'upload image_input')
            await input_image.wait_for(timeout=OPEN_URL_TIMEOUT, state='attached')
            await input_image.set_input_files(file)

            image_added = await self.get_visible_locator(page, 'upload image_added')
            await image_added.wait_for(timeout=OPEN_URL_TIMEOUT * wait_minute, state='visible')
            logger.info(f'一共要上传{len(image_files)}张图片, 首张图片上传成功: {file}')
            for index, file in enumerate(image_files[1:]):
                image_continue = await self.get_visible_locator(page, 'upload image_continue')
                # 处理文件选择对话框
                async with page.expect_file_chooser() as fc_info:
                    await image_continue.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(file)
                logger.info(f'第{index + 2}张图片上传成功: {file}')
            return page

    async def write_title(self, page: Page, content: str) -> Optional[Page]:
        """  """
        if content:
            logger.info('填写标题')
            input_title = await self.get_visible_locator(page, 'upload input_title')
            await input_title.click()
            await input_title.fill(content)
        else:
            logger.info('标题为空')
        return page

    async def write_describe(self, page: Page, content: str, labels: Tuple[str, ...]) -> Optional[Page]:
        """  """
        if content:
            content = content.replace('#', "'#'")
            logger.info('填写描述')
            input_describe = await self.get_visible_locator(page, 'upload input_describe')
            await input_describe.click()
            await page.keyboard.type(content)

            if len(labels) > 0:
                logger.info('填写标签【最多5个】')
                # 移动光标到文本末尾
                await page.keyboard.press('End')
                await page.keyboard.press('Enter')
                for label in labels[:5]:
                    logger.info(f'输入标签: {label}')
                    await input_describe.click()
                    await page.keyboard.press('End')
                    await page.keyboard.type('#')
                    await page.keyboard.type(label)
                    label_list = await self.get_visible_locators(page, 'upload input_describe label_list')
                    label_list = await label_list.all()
                    label1 = label_list[0]
                    await label1.click()
            else:
                logger.info('标签为空')
        else:
            logger.info('描述为空')
        return page

    async def set_location(self, page: Page, site: str = '') -> Optional[Page]:
        """  """
        if site:
            logger.info(f'设置地点: {site}')
            # 先点击, 然后才会弹出input元素
            click_location = await self.get_visible_locator(page, 'upload click_location')
            await click_location.click()
            input_location = page.locator(self.parser.get_xpath('upload click_location input_location'))
            await input_location.wait_for(timeout=OPEN_URL_TIMEOUT, state='attached')
            await page.keyboard.type('1')
            await page.keyboard.press('Backspace')
            await page.keyboard.type(site)
            locator = await self.get_visible_locator(page, 'upload click_location location')
            locator_text = await locator.inner_text()
            if '未搜索到' in locator_text or '无数据' in locator_text:
                logger.info('位置被未搜索到')
                await input_location.clear()
            else:
                await locator.click()
                await input_location.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')
        else:
            logger.info('不设置地点')
        return page

    async def set_theme(self, page: Page, theme: str = '') -> Optional[Page]:
        def parse_follow_count(text):
            # 匹配包含单位的跟拍数
            match = re.match(r'(\d+(?:\.\d+)?)\s*(万)?', text)
            if match:
                number = float(match.group(1))
                if match.group(2) == '万':
                    number *= 10000
                return int(number)
            return 0

        if theme:
            logger.info(f'设置贴纸: {theme}')
            # 先点击, 然后才会弹出input元素
            click_theme = await self.get_visible_locator(page, 'upload click_theme')
            await click_theme.click()
            input_theme = await self.get_visible_locator(page, 'upload click_theme input_theme')
            await input_theme.fill(theme)

            follow_counts = []
            theme_list = await self.get_visible_locators(page, 'upload click_theme theme_list')
            theme_list = await theme_list.all()
            for index, theme in enumerate(theme_list):
                content = await self.get_child_visible_locator(theme, 'upload click_theme theme_list _content')
                follow_count_text = await content.inner_text()
                follow_count = parse_follow_count(follow_count_text)
                follow_counts.append((follow_count, content))

            # 找到跟拍数最大值
            max_followed_theme = max(follow_counts, key=lambda x: x[0])[1]
            # 点击最大跟拍数的元素
            await max_followed_theme.click()
        else:
            logger.info('不设置贴纸')
        return page

    async def set_download(self, page: Page, save: bool) -> Optional[Page]:
        """  """
        logger.info(f'是否允许他人保存: {"是" if save else "否"}')
        if not save:
            download = await self.get_visible_locator(page, 'upload download')
            await download.locator('label').nth(1).click()
        return page

    async def set_permission(self, page: Page) -> Optional[Page]:
        """  """
        logger.info('设置权限: 公开')
        permission = await self.get_visible_locator(page, 'upload permission')
        await permission.locator('label').nth(0).click()
        return page

    async def set_time(self, page: Page) -> Optional[Page]:
        """  """
        logger.info('设置发布时间: 立即发布')
        upload_time = await self.get_visible_locator(page, 'upload time')
        await upload_time.locator('label').nth(0).click()
        return page

    async def click_publish(self, page: Page) -> Optional[Page]:
        """  """
        logger.info('点击发布')
        # 先等待视频检测完毕
        detecting = page.locator(self.parser.get_xpath('upload publish detecting'))
        detect_failed = page.locator(self.parser.get_xpath('upload publish detect_failed'))
        await detecting.wait_for(timeout=OPEN_URL_TIMEOUT, state='hidden')
        if await detect_failed.is_visible():
            logger.warning('视频检测失败, 继续发布视频')
        publish = await self.get_visible_locator(page, 'upload publish sure')
        await publish.click()
        return page


__all__ = ['DyUploader']
