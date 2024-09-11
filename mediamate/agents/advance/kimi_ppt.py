import os
import shutil

from playwright.async_api import async_playwright
from mediamate.tools.kimi.client import KimiClient
from mediamate.tools.convert.convert_to_image import ConvertToImage
from mediamate.config import config, ConfigManager
from mediamate.utils.log_manager import log_manager
from mediamate.utils.schema import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType
from mediamate.utils.const import TRACE_PLAYWRIGHT_DEV


logger = log_manager.get_logger(__file__)


class KimiPPT:
    def __init__(self, ppt_path: str):
        self.ppt_path = ppt_path
        self.convert = ConvertToImage()
        self.kimi_client = KimiClient()

    async def get_ppt(self,
                      headless: bool,
                      topic: str,
                      logo_path: str,
                      username: str,
                      scene: str,
                      style: str,
                      color_index: int,
                      card_index: int):
        """  """
        async with async_playwright() as p:
            context, page = await self.kimi_client.login(p, headless=headless)
            try:
                await self.kimi_client.get_ppt(page, self.ppt_path, topic, scene, style, color_index, card_index)
            except Exception as e:
                logger.error(e)
            finally:
                kimi_dir = f'{config.DATA_DIR}/active/kimi'
                os.makedirs(kimi_dir, exist_ok=True)
                filename = f'{kimi_dir}/trace_kimi.zip'
                await context.tracing.stop(path=filename)
                await context.close()
                logger.info(f'可进入查看跟踪结果: {TRACE_PLAYWRIGHT_DEV} , file: {filename}')
        if username and logo_path:
            self.ppt_path = self.kimi_client.update_ppt(ppt_path=self.ppt_path, logo_path=logo_path, username=username)
        return self.ppt_path

    async def save_to_xhs(self, metadata: dict):
        """ 保存到小红书上传目录 """
        media_config = config.MEDIA.get('media', {})
        xhs_config = media_config.get('xhs', [])
        for xhs in xhs_config:
            media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
            media_path = MediaPath(info=media_info)
            kimi_ppt_path = os.path.join(media_path.upload, 'kimi_ppt')
            if os.path.exists(kimi_ppt_path):
                shutil.rmtree(kimi_ppt_path)
            os.makedirs(kimi_ppt_path, exist_ok=True)

            await self.convert.ppt_to_images(self.ppt_path, kimi_ppt_path)
            metadata_config = ConfigManager(f'{kimi_ppt_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('地点', metadata.get('地点'))
            logger.info(f'数据已保存至: {kimi_ppt_path}')

    async def save_to_dy(self, metadata: dict):
        """ 保存到抖音上传目录 """
        media_config = config.MEDIA.get('media', {})
        dy_config = media_config.get('dy', [])
        for dy in dy_config:
            media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
            media_path = MediaPath(info=media_info)
            kimi_ppt_path = os.path.join(media_path.upload, 'kimi_ppt')
            if os.path.exists(kimi_ppt_path):
                shutil.rmtree(kimi_ppt_path)
            os.makedirs(kimi_ppt_path, exist_ok=True)

            await self.convert.ppt_to_images(self.ppt_path, kimi_ppt_path)
            metadata_config = ConfigManager(f'{kimi_ppt_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('音乐', metadata.get('音乐'))
            await metadata_config.set('地点', metadata.get('地点'))
            await metadata_config.set('贴纸', metadata.get('贴纸'))
            await metadata_config.set('允许保存', metadata.get('允许保存'))
            logger.info(f'数据已保存至: {kimi_ppt_path}')
