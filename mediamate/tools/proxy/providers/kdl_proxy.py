"""
This module provides the implementation of the KdlProxy class, which interacts with the KDL proxy service.
"""
import re
from typing import List, Tuple
import httpx

from mediamate.utils.log_manager import log_manager
from mediamate.tools.proxy.base import BaseProvider


logger = log_manager.get_logger(__file__)


class KdlProxy(BaseProvider):
    """
    KdlProxy interacts with the KDL proxy service to fetch and validate proxy IPs.
    """
    def __init__(self):
        """
        Initialize the KdlProxy with default values.
        """
        super().__init__(provider_name='KDL')
        self.base_url = "https://dps.kdlapi.com/"
        self.username = ''
        self.password = ''
        self.secret_id = ''
        self.secret_key = ''

    def set_params(self, username: str, password: str, secret_id: str, secret_key: str):
        """
        Set the configuration for the KDL proxy.

        Args:
            username (str): The username for the KDL proxy service.
            password (str): The password for the KDL proxy service.
            secret_id (str): The secret ID for the KDL proxy service.
            secret_key (str): The secret key for the KDL proxy service.

        Raises:
            ValueError: If any configuration parameter is missing.
        """
        self.username = username
        self.password = password
        self.secret_id = secret_id
        self.secret_key = secret_key
        if not all([self.username, self.password, self.secret_id, self.secret_key]):
            raise ValueError(f'The configuration parameters of {self.provider_name} are incorrect.')

    def parse_proxy(self, proxy_info: str) -> Tuple[str, int]:
        """
        Parse the KDL proxy information.

        Args:
            proxy_info (str): The proxy information string.

        Returns:
            Tuple[str, int]: A dictionary containing IP, port, and expiration time.

        Raises:
            ValueError: If the proxy information format is invalid.
        """
        proxies: List[str] = proxy_info.split(":")
        if len(proxies) != 2:
            raise ValueError("not invalid kuaidaili proxy info")

        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5}),(\d+)'
        match = re.search(pattern, proxy_info)
        if not match.groups():
            raise ValueError("not match kuaidaili proxy info")

        ip, port, ex = match.groups()
        return (f'http://{self.username}:{self.password}@{ip}:{port}', int(ex))

    async def get_direct_proxies(self, num: int) -> List[str]:
        """ 直接从代理商获取代理 """
        uri = "/api/getdps/"
        params = {
            "secret_id": self.secret_id,
            "signature": self.secret_key,
            "pt": 1,
            "format": "json",
            "sep": 1,
            "f_et": 1,
            "num": num
        }

        ip_infos: List[str] = []
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + uri, params=params)
            if response.status_code != 200:
                logger.error(f"[get_proxies] statuc code not 200 and response.txt:{response.text}")
                raise ValueError("get ip error from proxy provider and status code not 200 ...")

            ip_response = response.json()
            if ip_response.get("code") != 0:
                logger.error(f"[get_proxies]  code not 0 and msg:{ip_response.get('msg')}")
                raise ValueError("get ip error from proxy provider and code not 0 ...")

            proxy_list: List[str] = ip_response.get("data", {}).get("proxy_list")
            for proxy in proxy_list:
                https, ex = self.parse_proxy(proxy)
                ip_infos.append(https)
                ip_key = f"{self.provider_name}_{https.split('@')[1]}"
                # self.redis_client.set_data(ip_key, https, ex=ex)
                await self.client.set(ip_key, https, ex=ex)
        return ip_infos

    async def get_proxies(self, num: int) -> List[str]:
        """ 先从redis中获取代理, 不足部分从代理商获取 """
        uri = "/api/getdps/"

        # 优先从redis中拿 IP
        # ip_list = self.redis_client.keys(f'{self.provider_name}_*')
        ip_list = self.client.keys(f'{self.provider_name}_*')
        if len(ip_list) >= num:
            return ip_list[:num]

        # 如果缓存中的数量不够，从IP代理商获取补上，再存入缓存中
        need_count = num - len(ip_list)
        params = {
            "secret_id": self.secret_id,
            "signature": self.secret_key,
            "pt": 1,
            "format": "json",
            "sep": 1,
            "f_et": 1,
            "num": need_count
        }

        ip_infos: List[str] = []
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + uri, params=params)
            if response.status_code != 200:
                logger.error(f"[get_proxies] statuc code not 200 and response.txt:{response.text}")
                raise ValueError("get ip error from proxy provider and status code not 200 ...")

            ip_response = response.json()
            if ip_response.get("code") != 0:
                logger.error(f"[get_proxies]  code not 0 and msg:{ip_response.get('msg')}")
                raise ValueError("get ip error from proxy provider and  code not 0 ...")

            proxy_list: List[str] = ip_response.get("data", {}).get("proxy_list")
            for proxy in proxy_list:
                https, ex = self.parse_proxy(proxy)
                ip_infos.append(https)
                ip_key = f"{self.provider_name}_{https.split('@')[1]}"
                # self.redis_client.set_data(ip_key, https, ex=ex)
                await self.client.set(ip_key, https, ex=ex)
        return ip_list + ip_infos
