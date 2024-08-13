import requests
import json
from mediamate.tools.api_market.base import BaseMarket


class TextEmbeddingsOpenAI(BaseMarket):
    def __init__(self):
        super().__init__()

    def init(self, api_key, url: str='', model: str=''):
        self.api_key = api_key
        self.url = url or 'https://api.302.ai/v1/embeddings'
        self.model = model or 'text-embedding-3-large'
        return self

    def get_payload(self, text: str) -> str:
        """  """
        return json.dumps({
            'model': self.model,
            'input': text,
         })

    def get_headers(self) -> dict:
        """  """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

    def get_response(self, text: str):
        """  """
        return requests.request(
         'POST',
            self.url,
            headers=self.get_headers(),
            data=self.get_payload(text)
        )


if __name__ == '__main__':
    from mediamate.config import config
    api_key = config.get('302__APIKEY')

    ig = TextEmbeddingsOpenAI()
    ig.init(api_key)
    text = 'The food was delicious and the waiter...'
    response = ig.get_response(text)
    print(response.text)
