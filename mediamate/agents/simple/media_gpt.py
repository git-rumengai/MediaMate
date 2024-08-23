import os.path
from typing import List

from mediamate.utils.schemas import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType
from mediamate.tools.api_market.chat import Chat
from mediamate.tools.converter.convert_to_text import ConvertToText
from mediamate.tools.api_market.recognizer import OpenAIImageRecognizer, OpenAIAudioRecognizer
from mediamate.config import config, ConfigManager
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class MediaGPT:
    """ 输入本地图片/视频文件, 输出完整的图文准备文件 """
    def __init__(self):
        api_key = config.get('302__APIKEY')
        model = config.get('302__LLM')
        image_recognizer = OpenAIImageRecognizer(api_key=api_key)
        audio_recognizer = OpenAIAudioRecognizer(api_key=api_key)
        self.convert_to_text = ConvertToText(image_recognizer, audio_recognizer)
        self.chat = Chat(api_key=api_key, model=model)

    def prepare_image(self, prompt: str, images: List[str]) -> str:
        """  """
        for index, image in enumerate(images):
            logger.info(f'正在识别第{index+1}张图片: ')
            response = self.convert_to_text.read_file(image)
            logger.info(f'识别内容: {response}')
            prompt += f'\n图{index + 1}: {response}\n'
        logger.info(prompt)
        response = self.chat.get_response(prompt)
        return response

    def prepare_video(self, prompt: str, video: str) -> str:
        """  """
        response = self.convert_to_text.read_file(video)
        prompt = f'{prompt}\n###\n{response}\n###'
        logger.info(prompt)
        response = self.chat.get_response(prompt)
        return response

    async def save_to_xhs(self, metadata: dict):
        """ 保存到小红书上传目录 """
        media_config = config.MEDIA.get('media', {})
        for xhs in media_config.get('xhs', []):
            media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
            media_path = MediaPath(info=media_info)
            media_gpt_path = os.path.join(media_path.upload, 'media_gpt')
            metadata_config = ConfigManager(f'{media_gpt_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('地点', metadata.get('地点'))
            logger.info(f'数据已保存至: {media_gpt_path}')

    async def save_to_dy(self, metadata: dict):
        """ 保存到抖音上传目录 """
        media_config = config.MEDIA.get('media', {})
        for dy in media_config.get('dy', []):
            media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
            media_path = MediaPath(info=media_info)
            media_gpt_path = os.path.join(media_path.upload, 'media_gpt')
            metadata_config = ConfigManager(f'{media_gpt_path}/metadata.yaml')
            await metadata_config.set('标题', metadata.get('标题'))
            await metadata_config.set('描述', metadata.get('描述'))
            await metadata_config.set('标签', metadata.get('标签'))
            await metadata_config.set('音乐', metadata.get('音乐'))
            await metadata_config.set('地点', metadata.get('地点'))
            await metadata_config.set('贴纸', metadata.get('贴纸'))
            await metadata_config.set('允许保存', metadata.get('允许保存'))
            logger.info(f'数据已保存至: {media_gpt_path}')
