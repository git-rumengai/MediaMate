import requests
from typing import List
from pydantic import constr, Field, conlist, create_model

from mediamate.config import config
from mediamate.tools.api_market.chat import Chat
from mediamate.utils.llm_pydantic import llm_pydantic
from mediamate.utils.log_manager import log_manager
from mediamate.utils.enums import VideoOrientation


logger = log_manager.get_logger(__file__)


def create_response_model(number: int):
    if number <= 0:
        raise ValueError("number must be a positive integer")
    keywords_field = conlist(constr(strip_whitespace=True), min_length=number, max_length=number)
    model = create_model(
        'ResponseModel',
        keywords=(keywords_field, Field(..., description=f'按顺序创建 {number} 个与描述相关的"pexels"搜索词, 语言: 英文'))
    )
    return model


PHOTO_PROMPT = """
我想从"pexels"网站上寻找一张图片来描述这段内容: 
###
{text}
###

按照如下schema描述输出标准的JSON格式. 请确保JSON数据没有多余的空格和换行, 只包含最小的必要格式：
ResponseModel
"""

VIDEO_PROMPT = """
我想从"pexels"网站上寻找一段视频来描述这段内容: 
###
{text}
###

按照如下schema描述输出标准的JSON格式. 请确保JSON数据没有多余的空格和换行, 只包含最小的必要格式：
ResponseModel
"""


class FreePexels:
    def __init__(self, api_key: str = ''):
        self.api_key = api_key or config.get('PEXELS')
        assert self.api_key, '缺少配置: PEXELS'
        self.chat = Chat()

    def search_photos(self, query, orientation=None, size=None, color=None, locale: str = 'zh-CN', page=1, per_page=10):
        """  """
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "orientation": orientation,
            "size": size,
            "color": color,
            "locale": locale,
            "page": page,
            "per_page": per_page
        }
        params = {key: value for key, value in params.items() if value is not None}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error: {response.status_code} - {response.text}")
            return None

    def search_videos(self, query, orientation=None, size=None, locale: str = 'zh-CN', page=1, per_page=10):
        """  """
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "orientation": orientation,
            "size": size,
            "locale": locale,
            "page": page,
            "per_page": per_page
        }
        params = {key: value for key, value in params.items() if value is not None}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error: {response.status_code} - {response.text}")
            return None

    def get_photo(self, text: str, number: int = 1, orientation: VideoOrientation = VideoOrientation.LANDSCAPE) -> List[str]:
        """  """
        orientation = 'landscape' if orientation == VideoOrientation.LANDSCAPE else 'portrait'
        prompt = PHOTO_PROMPT.format(text=text)
        ResponseModel = create_response_model(number)
        parsed_data = llm_pydantic.get_llm_response(self.chat, prompt, ResponseModel)
        keywords = parsed_data.keywords
        result = []
        for keyword in keywords:
            search_result = self.search_photos(query=keyword, orientation=orientation, size='medium')
            photo = search_result['photos'][0]
            result.append(photo['src'][orientation])
        return result

    def get_video(self, text: str, number: int = 1, orientation: VideoOrientation = VideoOrientation.LANDSCAPE) -> List[str]:
        """ 給出指定数量时长最短的视频 """
        orientation = 'landscape' if orientation == VideoOrientation.LANDSCAPE else 'portrait'
        prompt = VIDEO_PROMPT.format(text=text)
        ResponseModel = create_response_model(number)
        parsed_data = llm_pydantic.get_llm_response(self.chat, prompt, ResponseModel)
        keywords = parsed_data.keywords
        result = []
        for keyword in keywords:
            search_results = self.search_videos(query=keyword, orientation=orientation, size='medium')
            videos = search_results['videos']
            # 按时长排序, 保留时长最短的
            sorted_videos = sorted(videos, key=lambda x: x['duration'])
            result.append(sorted_videos[0]['video_files'][0]['link'])
        return result
