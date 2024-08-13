from fake_useragent import UserAgent
from typing import Optional
from mediamate.tools.proxy import proxy_pool
from mediamate.config import config
from mediamate.utils.log_manager import log_manager

logger = log_manager.get_logger(__file__)


async def get_random_proxy() -> str:
    """
    使用代理优先级:
    1. 代理池
    2. 静态ip
    3. 不用代理
    """
    proxy = config.get('FIXED_PROXY', '')
    if config.get('PROXY_NAME'):
        proxy = await proxy_pool.get_random_proxy()
    return proxy


async def get_direct_proxy() -> str:
    """
    使用代理优先级:
    1. 代理池
    2. 静态ip
    3. 不用代理
    """
    proxy = config.get('FIXED_PROXY', '')
    if config.get('PROXY_NAME'):
        proxy = await proxy_pool.get_direct_proxy()
    return proxy


def proxy_to_playwright(proxy: str) -> Optional[dict]:
    result = None
    if proxy:
        user, server = proxy.split('//')[1].split('@')
        username, password = user.split(':')
        result = {"server": f'http://{server}', "username": username, "password": password,}
    return result


def get_useragent(pc: bool = True):
    """  """
    pf = 'pc' if pc else 'mobile'
    user_agent = UserAgent(browsers='chrome', os='windows', platforms=pf)
    return user_agent.chrome


if __name__ == '__main__':
    result = get_useragent()
    print(result)
