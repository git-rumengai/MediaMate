import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
import os
import shutil
import pandas as pd
import wbdata
from datetime import datetime

from mediamate.tools.chart_video import BarRace
from mediamate.config import config, ConfigManager
from mediamate.utils.schema import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


""" 
使用该示例需要先安装: wbdata
"""


def download_data() -> pd.DataFrame:
    """ 下载国家GDP数据 """
    # 设置日期范围
    countries = ['CN', 'US', 'JP', 'IN', 'RU', 'GB', 'FR', 'DE', 'IT', 'AU', 'KR', 'SG']
    indicators = {'NY.GDP.MKTP.CD': 'GDP'}

    start_date = datetime(1954, 1, 1)
    end_date = datetime(2024, 1, 1)
    # 获取 GDP 数据
    gdp_data = wbdata.get_dataframe(
        indicators=indicators,
        date=(start_date, end_date),
        country=countries,
        freq='M',
    )
    gdp_data = gdp_data.reset_index()
    gdp_data = gdp_data.pivot(index='date', columns='country', values='GDP')
    gdp_data = gdp_data / 1e8
    gdp_data.index = pd.to_datetime(gdp_data.index, format='%Y')
    return gdp_data


async def get_xhs_bar_race(reset: bool = False):
    """  """
    gdp_data = download_data()
    media_config = config.MEDIA.get('media', {})
    for xhs in media_config.get('xhs', []):
        media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
        media_path = MediaPath(info=media_info)
        bar_race_path = os.path.join(media_path.upload, 'bar_race')
        if reset:
            shutil.rmtree(bar_race_path, ignore_errors=True)
        os.makedirs(bar_race_path, exist_ok=True)
        filename = 'gdp_data.csv'
        gdp_data.to_csv(f'{bar_race_path}/{filename}')
        title = f'过去{gdp_data.shape[0]}年(GDP: 亿美元)'
        metadata = {
            '标题': title,
            '描述': '各国GPD历史变动',
            '标签': ('GPD', 'MediaMate', '经济数据'),
            '地点': '上海',

            'chart_video': {
                'filename': filename,
                'title': title,
                'plot_bgcolor': '#9CDCEB',
                'paper_bgcolor': 'rgba(200, 255, 255, 0.5)',
                'video_mode': [16, 9],
                'resolution': [1920, 1080],
                'fps': 3
            }
        }
        metadata_config = ConfigManager(f'{bar_race_path}/metadata.yaml')
        await metadata_config.set('标题', metadata.get('标题'))
        await metadata_config.set('描述', metadata.get('描述'))
        await metadata_config.set('标签', metadata.get('标签'))
        await metadata_config.set('地点', metadata.get('地点'))
        await metadata_config.set('chart_video', metadata.get('chart_video'))
        br = BarRace(bar_race_path)
        br.create_video()
        logger.info(f'数据已保存至: {bar_race_path}')
        break


async def get_dy_bar_race(reset: bool = False):
    """  """
    gdp_data = download_data()
    media_config = config.MEDIA.get('media', {})
    for dy in media_config.get('dy', []):
        media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
        media_path = MediaPath(info=media_info)
        bar_race_path = os.path.join(media_path.upload, 'bar_race')
        if reset:
            shutil.rmtree(bar_race_path, ignore_errors=True)
        os.makedirs(bar_race_path, exist_ok=True)

        filename = 'gdp_data.csv'
        gdp_data.to_csv(f'{bar_race_path}/{filename}')
        title = f'过去{gdp_data.shape[0]}年(GDP: 亿美元)'
        metadata = {
            '标题': title,
            '描述': '各国GPD历史变动',
            '标签': ('GPD', 'MediaMate', '经济数据'),
            '地点': '上海',
            '音乐': '热歌榜',
            '贴纸': '精选好房',
            '允许保存': '否',

            'chart_video': {
                'filename': filename,
                'title': title,
                'plot_bgcolor': 'rgba(240, 255, 255, 0.5)',
                'paper_bgcolor': 'rgba(200, 255, 255, 0.5)',
                'video_mode': [16, 9],
                'resolution': [1920, 1080],
                'fps': 3
            }
        }
        metadata_config = ConfigManager(f'{bar_race_path}/metadata.yaml')
        await metadata_config.set('标题', metadata.get('标题'))
        await metadata_config.set('描述', metadata.get('描述'))
        await metadata_config.set('标签', metadata.get('标签'))
        await metadata_config.set('地点', metadata.get('地点'))
        await metadata_config.set('chart_video', metadata.get('chart_video'))

        br = BarRace(bar_race_path)
        br.create_video()
        logger.info(f'数据已保存至: {bar_race_path}')
        break


if __name__ == '__main__':
    # result = download_data()
    # print(result)
    # asyncio.run(get_xhs_bar_race(reset=True))
    asyncio.run(get_dy_bar_race(reset=True))
