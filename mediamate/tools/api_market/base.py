from typing import Any
from abc import ABC, abstractmethod


class BaseMarket(ABC):
    def __init__(self, api_key: str, url: str = '', model: str = ''):
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
