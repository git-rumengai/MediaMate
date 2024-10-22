import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
from mediamate.platforms.dy.client import DyClient
from mediamate.config import config
from mediamate.utils.schema import MediaInfo
from mediamate.utils.enums import UrlType


async def run_dy():
    """  """
    media_config = config.MEDIA.get('media')
    if media_config:
        dy_config = media_config.get('dy', [])
        for i in dy_config:
            tasks = []
            if i.get('creator'):
                creator_client = DyClient(MediaInfo(url=UrlType.DY_CREATOR_URL, **i))
                tasks.append(creator_client.start_creator())
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(run_dy())
