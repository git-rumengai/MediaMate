import os
import subprocess
from mediamate.config import config
from mediamate.utils.enums import UrlType
from mediamate.utils.schema import MediaInfo, MediaPath


def show_trace(trace_path):
    """ 打开指定的 trace 文件 """
    command = f"playwright show-trace {trace_path}"
    subprocess.run(command, shell=True)


def open_trace(platform: str, url: UrlType, filename: str):
    media_config = config.MEDIA.get('media')
    if media_config:
        dy_config = media_config.get(platform, [])
        for i in dy_config:
            media_info = MediaInfo(url=url, **i)
            media_path = MediaPath(info=media_info)
            image_news_path = os.path.join(media_path.active, filename)
            show_trace(image_news_path)


if __name__ == "__main__":
    open_trace('dy', UrlType.DY_HOME_URL, 'trace_home.zip')
    # open_trace('dy', UrlType.DY_CREATOR_URL, 'trace_creator.zip')
    # open_trace('xhs', UrlType.XHS_HOME_URL, 'trace_home.zip')
    # open_trace('xhs', UrlType.XHS_CREATOR_URL, 'trace_creator.zip')
