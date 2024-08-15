import requests
import json
from typing import List
from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class KolorsImageGenerator(BaseMarket):
    def __init__(self):
        super().__init__()

    def init(self, api_key, url: str = '', model: str = ''):
        self.api_key = api_key
        self.url = url or 'https://api.302.ai/302/submit/kolors'
        self.model = model
        return self

    def get_payload(self, prompt: str, image_size: dict, **kwargs) -> str:
        """  """
        return json.dumps({
            'prompt': prompt,
            'image_size': image_size,
            **kwargs
        })

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
            'POST',
            self.url,
            headers=self.get_headers(),
            data=self.get_payload(prompt, image_size, **kwargs)
        )
        logger.info(response.text)
        if response.status_code == 200:
            return json.loads(response.text)['images']
        else:
            logger.error(response.text)
        return []


class DallesImageGenerator(BaseMarket):
    def __init__(self):
        super().__init__()

    def init(self, api_key, url: str = '', model: str = 'dall-e-3'):
        self.api_key = api_key
        self.url = url or 'https://api.302.ai/v1/images/generations'
        self.model = model
        return self

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

    def get_response(self, prompt: str, image_size: str='1024x1024', **kwargs) -> List[str]:
        """  """
        response = requests.request(
            'POST',
            self.url,
            headers=self.get_headers(),
            data=self.get_payload(prompt, image_size, **kwargs)
        )
        logger.info(response.text)
        if response.status_code == 200:
            return json.loads(response.text)['data']
        else:
            logger.error(response.text)
        return []
