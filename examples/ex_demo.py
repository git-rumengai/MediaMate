import asyncio
import os
import shutil
import requests
from mediamate.config import config, ConfigManager
from mediamate.utils.schemas import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


async def get_demo():
    """ 该脚本用来初始化一个发表图文的demo """
    # 1. 下载一张图片
    url = 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo311jqpqj76k005p19khr4c4688pl4em8?imageView2/2/w/540/format/webp|imageMogr2/strip2'
    response = requests.get(url)

    media_config = config.MEDIA.get('media', {})
    xhs_config = media_config.get('xhs', [])
    for xhs in xhs_config:
        media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
        media_path = MediaPath(info=media_info)
        demo_path = os.path.join(media_path.upload, 'demo')
        if os.path.exists(demo_path):
            shutil.rmtree(demo_path)
        os.makedirs(demo_path, exist_ok=True)
        with open(f'{demo_path}/rumengai.png', 'wb') as file:
            file.write(response.content)

        metadata = {
            '标题': '我为RuMengAI代言',
            '描述': '这只是个demo',
            '标签': ('AI社交', 'MediaMate', 'RPA'),
            '地点': '上海',
        }
        metadata_config = ConfigManager(f'{demo_path}/metadata.yaml')
        await metadata_config.set('标题', metadata.get('标题'))
        await metadata_config.set('描述', metadata.get('描述'))
        await metadata_config.set('标签', metadata.get('标签'))
        await metadata_config.set('地点', metadata.get('地点'))
        logger.info(f'数据已保存至: {demo_path}')
        break

    dy_config = media_config.get('dy', [])
    for dy in dy_config:
        media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
        media_path = MediaPath(info=media_info)
        demo_path = os.path.join(media_path.upload, 'demo')
        if os.path.exists(demo_path):
            shutil.rmtree(demo_path)
        os.makedirs(demo_path, exist_ok=True)
        with open(f'{demo_path}/rumengai.png', 'wb') as file:
            file.write(response.content)

        metadata = {
            '标题': '我为RuMengAI代言',
            '描述': '这只是个demo',
            '标签': ('AI社交', 'MediaMate', 'RPA'),
            '地点': '上海',
            '音乐': '热歌榜',
            '贴纸': '自动化',
            '允许保存': '否',
        }
        metadata_config = ConfigManager(f'{demo_path}/metadata.yaml')
        await metadata_config.set('标题', metadata.get('标题'))
        await metadata_config.set('描述', metadata.get('描述'))
        await metadata_config.set('标签', metadata.get('标签'))
        await metadata_config.set('音乐', metadata.get('音乐'))
        await metadata_config.set('地点', metadata.get('地点'))
        await metadata_config.set('贴纸', metadata.get('贴纸'))
        await metadata_config.set('允许保存', metadata.get('允许保存'))
        logger.info(f'数据已保存至: {demo_path}')
        break


if __name__ == '__main__':
    asyncio.run(get_demo())
