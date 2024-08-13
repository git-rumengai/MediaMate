"""
This module provides a ProxyPool class to manage and validate proxy IPs.
"""
import re
import random
import httpx
import logging
from typing import List, Optional

from mediamate.tools.proxy.providers.kdl_proxy import KdlProxy
from mediamate.tools.proxy.base import BaseProvider
from mediamate.utils.const import HTTP_BIN
from mediamate.config import config
from mediamate.utils.log_manager import log_manager

logger = log_manager.get_logger(__file__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def acheck_proxy(proxy: str) -> bool:
    """  """
    try:
        if not proxy:
            logger.info(f'未检测到代理')
            return False
        async with httpx.AsyncClient(proxies={'http://': proxy, 'https://': proxy}) as client:
            response = await client.get(HTTP_BIN)
            if response.status_code == 200:
                match = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b').search(proxy)
                if match:
                    logging.info(f'检测代理可用: {match.group()}')
                # 检测网速
                speed_response = await client.get('https://www.baidu.com')
                logging.info(f'网络延迟: {speed_response.elapsed.total_seconds()} seconds')
                return True
        return False
    except Exception as e:
        logger.error(f'检测代理报错: {e}')
        return False


class ProxyPool:
    """
    A class to manage a pool of proxy IPs and validate their availability.
    """
    def __init__(self):
        """
        Initialize the ProxyPool with default values.
        """
        self.proxy_list: List[str] = []
        self.ip_provider: BaseProvider = KdlProxy()
        self.init_provider()

    def init_provider(self):
        """
        Initialize the ProxyPool with default values.
        """
        if config.get('PROXY_NAME') == 'KDL':
            self.ip_provider = KdlProxy()
            username = config.get('KDL_USERNAME')
            password = config.get('KDL_PASSWORD')
            secret_id = config.get('KDL_SECRETID')
            secret_key = config.get('KDL_SECRETKEY')
            self.ip_provider.set_params(username, password, secret_id, secret_key)

    async def get_direct_proxy(self) -> Optional[str]:
        """  """
        for _ in range(5):
            proxy = await self.ip_provider.get_direct_proxies(1)
            proxy = proxy[0]
            if await acheck_proxy(proxy):
                return proxy
        logger.error('连续三次直接从代理商获取的代理无法使用, 请检查...')

    async def get_random_proxy(self) -> Optional[str]:
        """
        Retrieve a random proxy IP from the pool and validate its functionality.

        Returns:
            A valid proxy IP.

        Raises:
            ValueError: If no valid proxy IP can be found after checking all available IPs.
        """
        num = int(config.get("PROXY_BACKUP", 5))
        self.proxy_list = await self.ip_provider.get_proxies(num)
        while self.proxy_list:
            proxy = random.choice(self.proxy_list)
            self.proxy_list.remove(proxy)  # 取出来一个IP就应该移出掉
            if await acheck_proxy(proxy):
                return proxy
        logger.error('从代理池中获取的代理无法使用, 请重试...')
