import asyncio
import os
import glob
import random
from typing import Optional, Tuple, List
from playwright.async_api import Page

from mediamate.utils.const import OPEN_URL_TIMEOUT
from mediamate.utils.log_manager import log_manager
from mediamate.utils.schemas import MediaLoginInfo
from mediamate.config import config, ConfigManager
from mediamate.utils.enums import MediaType
from mediamate.platforms.base import BaseLocator


logger = log_manager.get_logger(__file__)


class XhsUploader(BaseLocator):
    """ 小红书发布页操作 """
    VIDEO_EXTENSIONS = ['*.mp4', '*.mov', '*.flv', '*.f4v', '*.mkv', '*.rm', '*.rmvb', '*.m4v', '*.mpg', '*.mpeg', '*.ts']
    IMAGE_EXTENSIONS = ['*.jpg', '*.jpeg', '*.png', '*.webp']

    def __init__(self):
        super().__init__()
        self.upload_data_dir: str = ''
        self.metadata_config: ConfigManager = ConfigManager()

    def init(self, info: MediaLoginInfo):
        """  """
        elements_path = f'{config.PROJECT_DIR}/platforms/static/elements/xhs/creator.yaml'
        super().init(elements_path)

        self.upload_data_dir = f'{config.DATA_DIR}/upload/xiaohongshu/{info.account}'
        os.makedirs(self.upload_data_dir, exist_ok=True)
        return self

    def check_upload_type(self) -> Tuple[MediaType, List[str]]:
        """  """
        self.metadata_config.init(f'{self.upload_data_dir}/metadata.yaml')
        title = self.metadata_config.get('标题')
        describe = self.metadata_config.get('描述')
        if not (title and describe):
            raise ValueError(f'发表信息数据不完整: {self.upload_data_dir}')

        image_files = []
        for extension in self.IMAGE_EXTENSIONS:
            image_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))
        if image_files:
            return MediaType.IMAGE, image_files
        else:
            video_files = []
            for extension in self.VIDEO_EXTENSIONS:
                video_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))
            if video_files:
                return MediaType.VIDEO, video_files
            else:
                raise ValueError(f'没有图片和视频文件, 无法发布: {self.upload_data_dir}')

    async def ensure_page(self, page: Page) -> Page:
        """  """
        return page

    async def click_upload_video(self, page: Page, wait_minute: int = 15) -> Optional[Page]:
        """  """
        logger.info('点击上传视频')
        steps = ('publish', )
        await self.ensure_step_page(page, steps)
        # 如果不刷新页面, 页面元素有未知变动, 后边无法填写标签
        await page.reload(timeout=OPEN_URL_TIMEOUT)
        steps = ('publish', 'publish video')
        await self.ensure_step_page(page, steps)

        video_files = []
        for extension in self.VIDEO_EXTENSIONS:
            video_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))
        # 如果没有视频文件，返回空列表
        if video_files:
            # 获取每个视频文件的大小并排序
            video_files_with_size = [(file, os.path.getsize(file)) for file in video_files]
            video_files_with_size.sort(key=lambda x: x[1])
            file = video_files_with_size[0][0]
            if len(video_files) > 1:
                logger.warning(f'视频文件超过一个, 默认选择最小的视频文件上传: {file}')

            video_input = await self.get_visible_locator(page, 'publish video input')
            await video_input.set_input_files(file)
            logger.info(f'正在上传: {file}')
            video_finish = await self.get_locator(page, 'publish video finish')
            await video_finish.wait_for(timeout=wait_minute * OPEN_URL_TIMEOUT, state='visible')
            logger.info(f'文件上传成功: {file}')
            return page

    async def click_upload_image(self, page: Page, wait_minute: int = 3) -> Optional[Page]:
        """  """
        logger.info('点击上传图文')
        steps = ('publish', )
        await self.ensure_step_page(page, steps)
        # 如果不刷新页面, 页面元素有未知变动, 后边无法填写标签
        await page.reload(timeout=OPEN_URL_TIMEOUT)
        steps = ('publish image', )
        await self.ensure_step_page(page, steps)

        image_files = []
        for extension in self.IMAGE_EXTENSIONS:
            image_files.extend(glob.glob(os.path.join(self.upload_data_dir, '**', extension), recursive=True))
        # 如果没有文件，返回空列表
        if image_files:
            if len(image_files) > 18:
                logger.warning(f'图片文件数量超过18, 只上传18张图片')
            file = image_files[0]
            image_input = await self.get_visible_locator(page, 'publish image input')
            await image_input.set_input_files(file)

            logger.info(f'一共要上传{len(image_files)}张图片, 首张图片上传成功: {file}')
            await asyncio.sleep(0.1)
            for index, file in enumerate(image_files[1:]):
                await asyncio.sleep(random.random()*0.3)
                add_more1 = await self.get_locator(page, 'publish image add_more1')
                add_more2 = await self.get_locator(page, 'publish image add_more2')
                if await add_more1.is_visible():
                    upload_button = add_more1
                else:
                    upload_button = add_more2
                # 处理文件选择对话框
                async with page.expect_file_chooser() as fc_info:
                    await upload_button.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(file)
                logger.info(f'第{index + 2}张图片上传: {file}')
            image_loading = await self.get_locator(page, 'publish image loading')
            image_loadings = await image_loading.all()
            for image in image_loadings:
                await image.wait_for(timeout=wait_minute * OPEN_URL_TIMEOUT, state='hidden')
            return page

    async def write_title(self, page: Page, content: str) -> Optional[Page]:
        """  """
        if content:
            logger.info('填写标题')
            input_title = await self.get_visible_locator(page, 'publish title')
            await input_title.click()
            await input_title.fill(content)
        else:
            logger.info('标题为空')
        return page

    async def write_describe(self, page: Page, content: str, labels: Tuple[str, ...] = ()) -> Optional[Page]:
        """  """
        if content:
            content = content.replace('#', "'#'")
            logger.info('填写描述')
            input_title = await self.get_visible_locator(page, 'publish describe')
            await input_title.click()
            await input_title.fill(content)

            if len(labels) > 0:
                logger.info('填写标签【最多5个】')
                # 移动光标到文本末尾
                await page.keyboard.press('End')
                await page.keyboard.press('Enter')
                for label in labels[:5]:
                    await page.keyboard.type('#')
                    # 等待标签列表出现
                    await page.keyboard.type(label)
                    label_list = await self.get_visible_locators(page, 'publish describe label_list')
                    await asyncio.sleep(0.1)
                    label_list = await label_list.all()
                    await label_list[0].click()
                    await page.keyboard.type(' ')
                    await page.keyboard.press('End')
            else:
                logger.info('标签为空')
        else:
            logger.info('描述为空')
        return page

    async def set_location(self, page: Page, site: str = '') -> Optional[Page]:
        """  """
        if site:
            logger.info(f'设置地点: {site}')
            location = await self.get_visible_locator(page, 'publish location')
            await location.click()
            await page.keyboard.type('1')
            await page.keyboard.press('Backspace')
            await page.keyboard.type(site)
            label_list = await self.get_visible_locators(page, 'publish location label_list')
            label_list = await label_list.all()
            await label_list[0].click()
            await label_list[0].wait_for(state='hidden')
        else:
            logger.info('不设置地点')
        return page

    async def set_permission(self, page: Page) -> Optional[Page]:
        """  """
        logger.info('设置权限: 公开')
        permission = await self.get_visible_locator(page, 'publish permission')
        await permission.click()
        return page

    async def set_time(self, page: Page) -> Optional[Page]:
        """  """
        logger.info('设置发布时间: 立即发布')
        permission = await self.get_visible_locator(page, 'publish time')
        await permission.click()
        return page

    async def click_publish(self, page: Page) -> Optional[Page]:
        """  """
        logger.info('点击发布')
        sure = await self.get_visible_locator(page, 'publish sure')
        await sure.click()
        await asyncio.sleep(0.1)
        # 图片不一定上传成功
        sure_loading = await self.get_locator(page, 'publish sure_loading')
        wait_sec = OPEN_URL_TIMEOUT / 1000
        while await sure.is_visible():
            if await sure.is_enabled():
                await sure.click()
            await asyncio.sleep(1)
            if await sure_loading.is_visible():
                logger.info('上传中...')
            wait_sec -= 1
            if wait_sec < 1:
                raise TimeoutError('发表失败...')
        return page


__all__ = ['XhsUploader']
