import requests
import json
from mediamate.tools.api_market.base import BaseMarket


class TextEmbeddingsOpenAI(BaseMarket):
    def __init__(self, api_key: str, model: str = ''):
        model = model or 'text-embedding-3-large'
        super().__init__(api_key=api_key, url='https://api.302.ai/v1/embeddings', model=model)

    def get_payload(self, text: str) -> str:
        """  """
        return json.dumps({'model': self.model, 'input': text,})

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
            method='POST',
            url=self.url,
            headers=self.get_headers(),
            data=self.get_payload(text)
        )
