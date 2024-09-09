import requests
import json
from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.log_manager import log_manager
from mediamate.config import config

logger = log_manager.get_logger(__file__)


class Chat(BaseMarket):
    def __init__(self, api_key: str = '', model: str = ''):
        model = model or 'gpt-4o-mini'
        super().__init__(api_key=api_key, url='https://api.302.ai/v1/chat/completions', model=model)

    def get_payload(self, message: str) -> str:
        """  """
        return json.dumps({"model": self.model, "message": message})

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
            method='POST',
            url=self.url,
            headers=self.get_headers(),
            data=self.get_payload(message)
        )
        logger.info(response.text)
        if response.status_code == 200:
            return json.loads(response.text)['output']
        else:
            logger.error(f'获取结果出错: {response.text}')
            return ''
