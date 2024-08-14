"""
This module contains the PhotoGPT class which is responsible for generating photo descriptions using AI,
and saving the generated photos to various platforms.
"""
import os.path
import requests
from typing import Tuple

from mediamate.tools.api_market.chat import Chat
from mediamate.tools.api_market.generator import KolorsImageGenerater
from mediamate.config import config, ConfigManager
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class PhotoGPT:
    """
    The PhotoGPT class handles generating photo descriptions using AI and saving the generated photos to various platforms.
    """
    def __init__(self):
        api_key = config.get('302__APIKEY')
        self.chat = Chat().init(api_key=api_key, model='deepseek-chat')
        self.kolors = KolorsImageGenerater().init(api_key=api_key)
        self.metadata = ConfigManager()

        self.prompt = ''
        self.media_config = {
            'title': '',
            'labels': [],
            'location': '上海',
            'theme': '',
            'wait_minute': 3,
            'download': '否'
        }
        self.text = self.get_text(self.prompt)
        self.image = self.get_image(self.text)

    def init(self, prompt: str):
        """
        Initialize the prompt for the AI model.

        :param prompt: The input prompt for the AI model.
        """
        self.prompt = prompt
        return self

    def init_media(self,
                   title: str = '',
                   labels: Tuple[str, ...] = (),
                   location: str = '',
                   wait_minute: int = 3,
                   theme: str = '',
                   download: str = '否'
                   ):
        """
        Initialize media configuration.

        :param title: The title of the media.
        :param labels: The labels for the media.
        :param location: The location for the media.
        :param wait_minute: The wait time in minutes.
        :param theme: The theme for the media.
        :param download: Whether the media can be downloaded.
        """
        self.media_config['title'] = title
        self.media_config['labels'] = list(labels)
        self.media_config['location'] = location or self.media_config['location']
        self.media_config['wait_minute'] = wait_minute or self.media_config['wait_minute']
        self.media_config['theme'] = theme or self.media_config['theme']
        self.media_config['download'] = download

        self.text = self.get_text(self.prompt)
        self.image = self.get_image(self.text)

        return self

    def get_text(self, message: str) -> str:
        """
        Get the text response from the AI chat model.

        :param message: The input message for the AI chat model.
        :return: The text response from the AI chat model.
        """
        return self.chat.get_response(message)

    def get_image(self, prompt: str):
        """
        Get the image response from the AI image generation model.

        :param prompt: The input prompt for the AI image generation model.
        :return: The image response from the AI image generation model.
        """
        response = self.kolors.get_response(prompt)
        return response

    async def save_to_xhs(self, seed: int = 1):
        """
        Save the generated photo to the XHS platform.

        :param seed: The seed for random selection of photo details.
        """
        image_url = self.image[0]['url']
        media_config = config.MEDIA.get('media')
        if media_config:
            for xhs in media_config.get('xhs', []):
                account = xhs['account']
                platform = xhs['platform']
                account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/photo_gpt'
                os.makedirs(account_dir, exist_ok=True)
                response = requests.get(image_url, timeout=10)
                with open(f'{account_dir}/{seed}.png', 'wb') as file:
                    file.write(response.content)
                self.metadata.init(f'{account_dir}/metadata.yaml')
                await self.metadata.set('标题', self.media_config['title'])
                await self.metadata.set('描述', self.text)
                await self.metadata.set('标签', self.media_config['labels'])
                await self.metadata.set('地点', self.media_config['location'])
                logger.info(f'数据已保存至: {account_dir}')

    async def save_to_dy(self, seed: int = 1):
        """
        Save the generated photo to the DY platform.

        :param seed: The seed for random selection of photo details.
        """
        image_url = self.image[0]['url']
        media_config = config.MEDIA.get('media')
        if media_config:
            for dy in media_config.get('dy', []):
                account = dy['account']
                platform = dy['platform']
                account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/photo_gpt'
                os.makedirs(account_dir, exist_ok=True)
                response = requests.get(image_url, timeout=10)
                with open(f'{account_dir}/{seed}.png', 'wb') as file:
                    file.write(response.content)
                self.metadata.init(f'{account_dir}/metadata.yaml')
                await self.metadata.set('标题', self.media_config['title'])
                await self.metadata.set('描述', self.text)
                await self.metadata.set('标签', self.media_config['labels'])
                await self.metadata.set('地点', self.media_config['location'])
                await self.metadata.set('贴纸', self.media_config['theme'])
                await self.metadata.set('允许保存', self.media_config['download'])
                logger.info(f'数据已保存至: {account_dir}')
