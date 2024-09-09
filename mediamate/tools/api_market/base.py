from typing import Any
from abc import ABC, abstractmethod
from mediamate.config import config


class BaseMarket(ABC):
    def __init__(self, api_key: str = '', url: str = '', model: str = ''):
        api_key = api_key or config.get('302__APIKEY', '')
        model = model or config.get('302__LLM', '')
        assert api_key, '缺少配置: 302__APIKEY'
        assert model, '缺少配置: 302__LLM'

        self.api_key = api_key
        self.url = url
        self.model = model

    @abstractmethod
    def get_payload(self, *args, **kwargs) -> str | dict:
        """  """

    @abstractmethod
    def get_headers(self, *args, **kwargs) -> dict:
        """  """

    @abstractmethod
    def get_response(self, *args, **kwargs) -> Any:
        """  """
