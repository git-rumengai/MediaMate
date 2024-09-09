import sys
import os

pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
from playwright.async_api import async_playwright

from mediamate.platforms.dy.client import DyClient
from mediamate.platforms.xhs.client import XhsClient
from mediamate.utils.schema import MediaInfo, UrlType
from mediamate.config import config
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__name__)


async def run_config():
    """  """
    async with async_playwright() as p:
        media_config = config.MEDIA.get('media')
        if media_config:
            xhs_config: list = media_config.get('xhs', [])
            dy_config: list = media_config.get('dy', [])
            tasks = []
            print(xhs_config)
            while True:
                if not(dy_config or xhs_config):
                    break
                if xhs_config:
                    xhs = xhs_config.pop()
                    if xhs.get('home'):
                        xhs_home_client = XhsClient(MediaInfo(url=UrlType.XHS_HOME_URL, **xhs))
                        tasks.append(xhs_home_client.start_home(p))
                    if xhs.get('creator'):
                        print(xhs)
                        xhs_creator_client = XhsClient(MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs))
                        tasks.append(xhs_creator_client.start_creator(p))
                if dy_config:
                    dy = dy_config.pop()
                    if dy.get('home'):
                        home_client = DyClient(MediaInfo(url=UrlType.DY_HOME_URL, **dy))
                        tasks.append(home_client.start_home(p))
                    if dy.get('creator'):
                        creator_client = DyClient(MediaInfo(url=UrlType.DY_CREATOR_URL, **dy))
                        tasks.append(creator_client.start_creator(p))
                await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(run_config())
