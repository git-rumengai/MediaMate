import os.path
import requests
import shutil
from typing import List
from mediamate.tools.api_market.generator import OpenAIImageGenerator
from mediamate.config import config, ConfigManager
from mediamate.utils.schemas import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class LogoGPT:
    """ 根据传入的LOGO提示词设计LOGO, 可同时输入多个提示词 """
    def __init__(self):
        api_key = config.get('302__APIKEY')
        self.image_generator = OpenAIImageGenerator(api_key=api_key)
        self.image = []

    def get_image(self, prompt: str) -> List[dict]:
        """ 获取图片 """
        response = self.image_generator.get_response(prompt)
        return response

    async def save_to_xhs(self, metadata: dict, prompts: List[str]):
        """ 保存到小红书上传目录 """
        if len(self.image) == 0:
            for prompt in prompts:
                image_response = self.get_image(prompt)
                self.image.append(image_response)
        media_config = config.MEDIA.get('media', {})
        for xhs in media_config.get('xhs', []):
            media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
            media_path = MediaPath(info=media_info)
            logo_gpt_path = os.path.join(media_path.upload, 'logo_gpt')
            if os.path.exists(logo_gpt_path):
                shutil.rmtree(logo_gpt_path)
            os.makedirs(logo_gpt_path, exist_ok=True)

            for index, image in enumerate(self.image):
                image_url = image[0]['url']
                response = requests.get(image_url, timeout=60)
                with open(f'{logo_gpt_path}/{index}.png', 'wb') as file:
                    file.write(response.content)
            metadata_config = ConfigManager(f'{logo_gpt_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('地点', metadata.get('地点'))
            logger.info(f'数据已保存至: {logo_gpt_path}')

    async def save_to_dy(self, metadata: dict, prompts: List[str]):
        """ 保存到抖音上传目录 """
        if len(self.image) == 0:
            for prompt in prompts:
                image_response = self.get_image(prompt)
                self.image.append(image_response)
        media_config = config.MEDIA.get('media', {})
        for dy in media_config.get('dy', []):
            media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
            media_path = MediaPath(info=media_info)
            logo_gpt_path = os.path.join(media_path.upload, 'logo_gpt')
            if os.path.exists(logo_gpt_path):
                shutil.rmtree(logo_gpt_path)
            os.makedirs(logo_gpt_path, exist_ok=True)

            for index, image in enumerate(self.image):
                image_url = image[0]['url']
                response = requests.get(image_url, timeout=60)
                with open(f'{logo_gpt_path}/{index}.png', 'wb') as file:
                    file.write(response.content)
            metadata_config = ConfigManager(f'{logo_gpt_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('音乐', metadata.get('音乐'))
            await metadata_config.set('地点', metadata.get('地点'))
            await metadata_config.set('贴纸', metadata.get('贴纸'))
            await metadata_config.set('允许保存', metadata.get('允许保存'))
            logger.info(f'数据已保存至: {logo_gpt_path}')
