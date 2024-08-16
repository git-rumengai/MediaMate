import asyncio
from mediamate.platforms.dy.client import DyClient
from mediamate.platforms.xhs.client import XhsClient
from mediamate.utils.schemas import MediaLoginInfo
from mediamate.config import config
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__name__)


async def run_xhs():
    """
    Initialize and run the XHS client for base and creator functionalities.

    Creates an instance of the XHS client and starts base and creator functionalities
    for each client based on the configuration.
    """
    xhs_client = XhsClient()
    media_config = config.MEDIA.get('media')
    if media_config:
        xhs_config = media_config.get('xhs', [])
        for i in xhs_config:
            xhs_client.init(MediaLoginInfo(**i))
            if i.get('base'):
                await xhs_client.start_base()
            if i.get('creator'):
                await xhs_client.start_creator()


async def run_dy():
    """
    Initialize and run the DY client for base and creator functionalities.

    Creates an instance of the DY client and starts base and creator functionalities
    for each client based on the configuration.
    """
    dy_client = DyClient()
    media_config = config.MEDIA.get('media')
    if media_config:
        dy_config = media_config.get('dy', [])
        for i in dy_config:
            dy_client.init(MediaLoginInfo(**i))
            if i.get('base'):
                await dy_client.start_base()
            if i.get('creator'):
                await dy_client.start_creator()


async def run_config():
    """
    Asynchronously run the configuration for both XHS and DY clients.

    Executes XHS and DY client configurations concurrently and handles any exceptions
    that may occur.
    """
    await run_xhs()
    await run_dy()


if __name__ == '__main__':
    asyncio.run(run_config())
