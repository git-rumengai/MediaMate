import requests
import json
from typing import Literal
from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class OpenAIImageRecognizer(BaseMarket):
    def __init__(self, api_key: str = '', model: str = ''):
        model = model or 'gpt-4o'
        super().__init__(api_key=api_key, url='https://api.302.ai/v1/chat/completions', model=model)

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
            method='POST',
            url=self.url,
            headers=self.get_headers(),
            data=self.get_payload(image_url)
        )
        if response.status_code == 200:
            return json.loads(response.text)['choices'][0]['message']['content']
        else:
            logger.error(f'获取结果出错: {response.text}')
            return ''


class OpenAIAudioRecognizer(BaseMarket):
    def __init__(self, api_key: str = '', model: str = ''):
        model = model or 'whisper-1'
        super().__init__(api_key=api_key, url='https://api.302.ai/v1/audio/transcriptions', model=model)

    def get_payload(self, language: str, response_format: Literal['json', 'text', 'srt', 'verbose_json', 'vtt'] = 'json', **kwargs) -> dict:
        """  """
        return {'model': self.model, 'response_format': response_format, 'language': language}

    def get_headers(self) -> dict:
        """  """
        return {'Authorization': f'Bearer {self.api_key}', 'User-Agent': 'Apifox/1.0.0 (https://apifox.com)', 'Accept': 'application/json'}

    def get_response(self, filename: str, language: str = 'zh', response_format: Literal['json', 'text', 'srt', 'verbose_json', 'vtt'] = 'json', **kwargs) -> {}:
        """  """
        print(self.get_payload(language, response_format))
        response = requests.request(
            method='POST',
            url=self.url,
            headers=self.get_headers(),
            data=self.get_payload(language, response_format),
            files={'file': open(filename, 'rb')}
        )
        print(response.text)
        if response.status_code == 200:
            return json.loads(response.text)['text']
        else:
            logger.error(response.text)
        return {}


if __name__ == '__main__':
    recognizer = OpenAIAudioRecognizer()
    filename = r'C:\Users\Admin\Desktop\123.wav'
    result = recognizer.get_response(filename, response_format='srt')
    print(result)
