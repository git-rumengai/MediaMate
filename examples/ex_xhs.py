import asyncio
from mediamate.platforms.xhs.client import XhsClient
from mediamate.config import config
from mediamate.utils.schemas import MediaInfo
from mediamate.utils.enums import UrlType


async def run_xhs():
    """  """
    media_config = config.MEDIA.get('media')
    if media_config:
        xhs_config = media_config.get('xhs', [])
        for i in xhs_config:
            tasks = []
            if i.get('home'):
                xhs_home_client = XhsClient(MediaInfo(url=UrlType.XHS_HOME_URL, **i))
                tasks.append(xhs_home_client.start_home())
            if i.get('creator'):
                xhs_creator_client = XhsClient(MediaInfo(url=UrlType.XHS_CREATOR_URL, **i))
                tasks.append(xhs_creator_client.start_creator())
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(run_xhs())
