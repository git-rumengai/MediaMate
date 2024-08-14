import asyncio
from mediamate.platforms.dy.client import DyClient
from mediamate.config import config
from mediamate.utils.schemas import MediaLoginInfo


if __name__ == '__main__':
    dy_client = DyClient()
    media_config = config.MEDIA.get('media')
    if media_config:
        dy_config = media_config.get('dy', [])
        for i in dy_config:
            dy_client.init(MediaLoginInfo(**i))
            if i.get('base'):
                asyncio.run(dy_client.start_base())
            if i.get('creator'):
                asyncio.run(dy_client.start_creator())
