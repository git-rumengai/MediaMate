"""
This module defines the base classes for proxy providers and IP information models.
"""

from abc import ABC, abstractmethod
from typing import List

# from mediamate.utils.redis_client import RedisClient
from mediamate.utils.const import REDIS_PROXY_DB
from mediamate.config import config, ConfigManager


# pylint: disable=R0903
class BaseProvider(ABC):
    """
    Abstract base class for proxy providers. All proxy providers should inherit from this class and
    implement the required methods to set configuration and get proxies.
    """
    def __init__(self, provider_name, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Initialize the base provider with a provider name.

        :param provider_name: Name of the proxy provider.
        """
        self.provider_name = provider_name
        # self.redis_client = RedisClient().init(REDIS_PROXY_DB)
        self.client = ConfigManager(f'{config.DATA_DIR}/active/proxy_pool.yaml')

    @abstractmethod
    async def get_direct_proxies(self, num: int) -> List[str]:
        """ """

    @abstractmethod
    async def get_proxies(self, num: int) -> List[str]:
        """  """
