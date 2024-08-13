import asyncio
from mediamate.platforms.xhs.client import XhsClient
from mediamate.config import config
from mediamate.utils.schemas import MediaLoginInfo


if __name__ == '__main__':
    xhs_client = XhsClient()
    media_config = config.MEDIA.get('media')
    if media_config:
        xhs_config = media_config.get('xhs', [])
        for i in xhs_config:
            xhs_client.init(MediaLoginInfo(**i))
            asyncio.run(xhs_client.start_base())
            asyncio.run(xhs_client.start_creator())
