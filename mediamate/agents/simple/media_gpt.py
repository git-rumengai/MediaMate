import base64
import json
from mimetypes import guess_type
import os.path
import requests
from typing import Tuple, List

from mediamate.tools.api_market.chat import Chat
from mediamate.tools.converter.convert_to_text import ConvertToText
from mediamate.tools.api_market.recognizer import ImageRecognizer, MediaRecognizer
from mediamate.config import config, ConfigManager
from mediamate.utils.log_manager import log_manager



logger = log_manager.get_logger(__file__)


class MediaGPT:
    """ 输入本地图片/视频文件, 输出完整的图文准备文件 """
    def __init__(self):
        api_key = config.get('302__APIKEY')

        image_recognizer = ImageRecognizer().init(api_key=api_key)
        media_recognizer = MediaRecognizer().init(api_key=api_key)
        self.convert_to_text = ConvertToText().init(image_recognizer, media_recognizer)
        self.chat = Chat().init(api_key=api_key, model='deepseek-chat')
        self.metadata = ConfigManager()

        self.prompt = ''
        self.media_config = {
            'title': '',
            'desc': '',
            'labels': ['RuMengAI', ],
            'location': '上海',
            'theme': '',
            'wait_minute': 3,
            'download': '否'
        }

    def init(self, prompt: str):
        """
        Initialize the prompt for the AI model.

        :param prompt: The input prompt for the AI model.
        """
        self.prompt = prompt
        return self

    def init_media(self,
                   title: str = '',
                   describe: str = '',
                   labels: Tuple[str, ...] = (),
                   location: str = '',
                   wait_minute: int = 3,
                   theme: str = '',
                   download: str = '否'
                   ):
        """
        Initialize media configuration.
        """
        self.media_config['title'] = title or self.media_config['title']
        self.media_config['desc'] = describe or self.media_config['desc']
        self.media_config['labels'] = list(labels) or self.media_config['labels']
        self.media_config['location'] = location or self.media_config['location']
        self.media_config['wait_minute'] = wait_minute or self.media_config['wait_minute']
        self.media_config['theme'] = theme or self.media_config['theme']
        self.media_config['download'] = download or self.media_config['download']
        return self

    def get_text(self, message: str) -> str:
        """
        Get the text response from the AI chat model.

        :param message: The input message for the AI chat model.
        :return: The text response from the AI chat model.
        """
        return self.chat.get_response(message)

    def prepare_image(self, images: List[str]) -> str:
        """  """
        prompt = self.prompt
        for index, image in enumerate(images):
            logger.info(f'正在识别第{index+1}张图片: ')
            response = self.convert_to_text.read_file(image)
            logger.info(f'识别内容: {response}')
            prompt += f'\n图{index + 1}: {response}\n'
        logger.info(prompt)
        response = self.chat.get_response(prompt)
        return response

    def prepare_video(self, video: str) -> str:
        """
        Get the image response from the AI image generation model.

        :param prompt: The input prompt for the AI image generation model.
        :return: The image response from the AI image generation model.
        """
        response = self.convert_to_text.read_file(video)
        prompt = f'{self.prompt}\n###\n{response}\n###'
        logger.info(prompt)
        response = self.chat.get_response(prompt)
        return response

    async def save_to_xhs(self, account_dir: str):
        """
        Save the generated photo to the XHS platform.
        """
        self.metadata.init(f'{account_dir}/metadata.yaml')
        await self.metadata.set('标题', self.media_config['title'])
        await self.metadata.set('描述', self.media_config['desc'])
        await self.metadata.set('标签', self.media_config['labels'])
        await self.metadata.set('地点', self.media_config['location'])
        logger.info(f'数据已保存至: {account_dir}')

    async def save_to_dy(self, account_dir: str):
        """
        Save the generated photo to the DY platform.
        """
        self.metadata.init(f'{account_dir}/metadata.yaml')
        await self.metadata.set('标题', self.media_config['title'])
        await self.metadata.set('描述', self.media_config['desc'])
        await self.metadata.set('标签', self.media_config['labels'])
        await self.metadata.set('地点', self.media_config['location'])
        await self.metadata.set('贴纸', self.media_config['theme'])
        await self.metadata.set('允许保存', self.media_config['download'])
        logger.info(f'数据已保存至: {account_dir}')
