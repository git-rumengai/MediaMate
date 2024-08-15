import requests
import json
from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class Chat(BaseMarket):
    def __init__(self, ):
       super().__init__()

    def init(self, api_key, url: str='', model: str=''):
        url = url or 'https://api.302.ai/v1/chat/completions'
        model = model or 'gpt-4o-mini'
        super().init(api_key, url, model)
        self.api_key = api_key
        self.url = url
        self.model = model
        return self

    def get_payload(self, message: str) -> str:
       """  """
       return json.dumps({
          "model": self.model,
          "message": message
       })

    def get_headers(self) -> dict:
        """  """
        return {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

    def get_response(self, message: str) -> str:
        """  """
        response = requests.request(
           'POST',
            self.url,
            headers=self.get_headers(),
            data=self.get_payload(message)
        )
        logger.info(response.text)
        if response.status_code == 200:
            return json.loads(response.text)['output']
        else:
            logger.error(f'获取结果出错: {response.text}')
            return ''
