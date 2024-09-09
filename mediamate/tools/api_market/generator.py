import requests
import json
from typing import List, Literal
from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class KolorsImageGenerator(BaseMarket):
    def __init__(self, api_key: str = ''):
        super().__init__(api_key=api_key, url='https://api.302.ai/302/submit/kolors')

    def get_payload(self, prompt: str, image_size: dict, **kwargs) -> str:
        """  """
        return json.dumps({'prompt': prompt, 'image_size': image_size, **kwargs})

    def get_headers(self) -> dict:
        """  """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

    def get_response(self, prompt: str, image_size: dict = {'width': 1024, 'height': 1024}, **kwargs) -> List[str]:
        """  """
        response = requests.request(
            method='POST',
            url=self.url,
            headers=self.get_headers(),
            data=self.get_payload(prompt, image_size, **kwargs)
        )
        logger.info(response.text)
        if response.status_code == 200:
            return json.loads(response.text)['images']
        else:
            logger.error(response.text)
        return []


class OpenAIImageGenerator(BaseMarket):
    def __init__(self, api_key: str = '', model: str = ''):
        model = model or 'dall-e-3'
        super().__init__(api_key=api_key, url='https://api.302.ai/v1/images/generations', model=model)

    def get_payload(self, prompt: str, image_size: str, **kwargs) -> str:
        """  """
        return json.dumps({
           "prompt": prompt,
           "n": 1,
           "model": self.model,
           "size": image_size
        })

    def get_headers(self) -> dict:
        """  """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

    def get_response(self, prompt: str, image_size: str = '1024x1024', **kwargs) -> List[dict]:
        """  """
        response = requests.request(
            method='POST',
            url=self.url,
            headers=self.get_headers(),
            data=self.get_payload(prompt, image_size, **kwargs)
        )
        logger.info(response.text)
        if response.status_code == 200:
            return json.loads(response.text)['data']
        else:
            logger.error(response.text)
        return []


class OpenAIAudioGenerator(BaseMarket):
    """  """
    def __init__(self, api_key: str = '', model: str = ''):
        model = model or 'tts-1-hd'
        super().__init__(api_key=api_key, url='https://api.302.ai/v1/audio/speech', model=model)

    def get_payload(self, prompt: str, voice: str = 'alloy', **kwargs) -> str:
        """  """
        return json.dumps({
           'model': self.model,
           'input': prompt,
           'voice': voice
        })

    def get_headers(self) -> dict:
        """  """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

    def get_response(self, prompt: str, voice: Literal['alloy', 'echo', 'fable', 'onyx', 'nova'] = 'alloy', **kwargs) -> bytes:
        """  """
        response = requests.request(
            method='POST',
            url=self.url,
            headers=self.get_headers(),
            data=self.get_payload(prompt, voice, **kwargs)
        )
        if response.status_code == 200:
            return response.content
        else:
            logger.error(response.text)
        return b''
