import requests
import json
from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class ImageRecognizer(BaseMarket):
    def __init__(self, ):
       super().__init__()

    def init(self, api_key, url: str = '', model: str = 'gpt-4o'):
        url = url or 'https://api.302.ai/v1/chat/completions'
        model = model or 'gpt-4o-mini'
        super().init(api_key, url, model)
        self.api_key = api_key
        self.url = url
        self.model = model
        return self

    def get_payload(self, image_url: str) -> str:
       """  """
       return json.dumps({
           "model": self.model,
           "stream": False,
           "messages": [
              {
                 "role": "user",
                 "content": [
                    {
                       "type": "text",
                       "text": "这张图片有什么？"
                    },
                    {
                       "type": "image_url",
                       "image_url": {
                          "url": image_url
                       }
                    }
                 ]
              }
           ]
        })

    def get_headers(self) -> dict:
        """  """
        return {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

    def get_response(self, image_url: str) -> str:
        """  """
        response = requests.request(
           'POST',
            self.url,
            headers=self.get_headers(),
            data=self.get_payload(image_url)
        )
        if response.status_code == 200:
            return json.loads(response.text)['choices'][0]['message']['content']
        else:
            logger.error(f'获取结果出错: {response.text}')
            return ''


class MediaRecognizer(BaseMarket):
    def __init__(self):
        super().__init__()

    def init(self, api_key, url: str='', model: str=''):
        self.api_key = api_key
        self.url = url or 'https://api.302.ai/v1/audio/transcriptions'
        self.model = model or 'whisper-1'
        return self

    def get_payload(self, **kwargs) -> str:
        """  """

    def get_headers(self) -> dict:
        """  """

    def get_response(self, filename: str, language: str='zh', **kwargs) -> {}:
        """  """
        response = requests.request(
            'POST',
            self.url,
            headers={'Authorization': f'Bearer {self.api_key}', 'User-Agent': 'Apifox/1.0.0 (https://apifox.com)', 'Accept': 'application/json'},
            data={'model': self.model, 'response_format': 'json', 'language': language},
            files={"file": open(filename, "rb")}
        )
        if response.status_code == 200:
            return json.loads(response.text)['text']
        else:
            logger.error(response.text)
        return {}
