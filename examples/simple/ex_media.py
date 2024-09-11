import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
import os
import requests
import shutil
from pydantic import BaseModel, Field, constr, field_validator
from typing import List
from mediamate.agents.simple.media_gpt import MediaGPT
from mediamate.utils.log_manager import log_manager
from mediamate.config import config
from mediamate.utils.llm_pydantic import llm_pydantic
from mediamate.utils.common import get_media_type
from mediamate.utils.schema import MediaInfo, MediaPath
from mediamate.utils.enums import UrlType
from mediamate.utils.enums import MediaType


logger = log_manager.get_logger(__file__)


class ResponseModel(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=18) = Field(..., description="标题要有吸引力")
    description: constr(strip_whitespace=True, max_length=200) = Field(..., description="简洁明了的描述，内容不超过200字符")
    keywords: List[constr(strip_whitespace=True, min_length=1, max_length=20)] = Field(..., description="关键词列表，不超过3个")

    @field_validator('keywords')
    def validate_keywords_length(cls, v):
        if len(v) > 3:
            raise ValueError('关键词数量不能超过3个')
        return v


IMAGES_PROMPT = f"""
根据给出的一组图片内容帮我生成一篇主题为"下午茶"的小红书风格文案。

按照如下schema描述输出标准的JSON格式. 请确保JSON数据没有多余的空格和换行, 只包含最小的必要格式：
ResponseModel

图片描述：
"""

VIDEO_PROMPT = f"""
根据这个视频内容帮我生成一篇主题为"精选好房"的抖音风格文案。

按照如下schema描述输出标准的JSON格式. 请确保JSON数据没有多余的空格和换行, 只包含最小的必要格式：
ResponseModel

视频描述：
"""

IMAGES = [
    'https://ss2.meipian.me/users/2531394/8b3ab230-4016-11eb-a090-d76407546a82.jpg',
    'https://p3.toutiaoimg.com/origin/pgc-image/303f5bc0b48249f094c2f7f5d4ae3a04?from=pc'
]

VIDEO = 'https://www.douyin.com/aweme/v1/play/?file_id=d35918c6c3554907982cb23c6a9d8059&is_play_url=1&line=0&sign=6c432f512bbc4e0fa7a420cf1a8d6fa3&source=PackSourceEnum_PUBLISH&uifid=3c3e9d4a635845249e00419877a3730e2149197a63ddb1d8525033ea2b3354c2fcb74766499cf3c6f79cb8aaebb8ad2f238d9adf46a107ca2cab64707cde3df42bbe0ddf12d441dcd90a0b8277bb88cf9e8e238a05cdb6085c040435f1bde20f7b466e80aa73aecfc457e3d188b457bcf2ea3af492b50f2cebfa4fc6dc1381a91632e2ce795d99aa474d7ce90f615e1189052baa9b1af5df6f12fb2b62740db6&video_id=v0200fg10000cqpn837og65jf3ve9fbg&aid=6383'


def download_media():
    """ 下载示例内容, 组图保存到xhs, 视频保存到dy """
    media_config = config.MEDIA.get('media', {})
    for xhs in media_config.get('xhs', []):
        media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
        media_path = MediaPath(info=media_info)
        media_gpt_image = os.path.join(media_path.upload, 'media_gpt')
        if os.path.exists(media_gpt_image):
            shutil.rmtree(media_gpt_image)
        os.makedirs(media_gpt_image, exist_ok=True)
        for index, image_url in enumerate(IMAGES):
            response = requests.get(image_url, timeout=30)
            with open(f'{media_gpt_image}/{index}.jpg', 'wb') as file:
                file.write(response.content)
        break

    response = requests.get(VIDEO, timeout=60)
    for dy in media_config.get('dy', []):
        media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
        media_path = MediaPath(info=media_info)
        media_gpt_video = os.path.join(media_path.upload, 'media_gpt')
        if os.path.exists(media_gpt_video):
            shutil.rmtree(media_gpt_video)
        os.makedirs(media_gpt_video, exist_ok=True)
        with open(f'{media_gpt_video}/1.mp4', 'wb') as file:
            file.write(response.content)
        break


async def get_media_gpt_image():
    """ 图片识别, 基于大模型 """
    media_gpt = MediaGPT()
    media_config = config.MEDIA.get('media', {})
    for xhs in media_config.get('xhs', []):
        media_info = MediaInfo(url=UrlType.XHS_CREATOR_URL, **xhs)
        media_path = MediaPath(info=media_info)
        media_gpt_image = os.path.join(media_path.upload, 'media_gpt')
        if not os.path.exists(media_gpt_image):
            logger.info(f'文件夹不存在: {media_gpt_image}')
            continue

        images = [os.path.join(media_gpt_image, i) for i in os.listdir(media_gpt_image) if get_media_type(i) == MediaType.IMAGE]
        parsed_data = media_gpt.prepare_image(IMAGES_PROMPT, images, ResponseModel)
        metadata = {
            '标题': parsed_data.title,
            '描述': parsed_data.description,
            '标签': tuple(parsed_data.keywords),
            '地点': '上海',
            '允许保存': '否',
        }
        await media_gpt.save_to_xhs(metadata)


async def get_media_gpt_video():
    """ 视频识别: 基于语音识别 """
    media_gpt = MediaGPT()
    media_config = config.MEDIA.get('media', {})
    for dy in media_config.get('dy', []):
        media_info = MediaInfo(url=UrlType.DY_CREATOR_URL, **dy)
        media_path = MediaPath(info=media_info)
        media_gpt_video = os.path.join(media_path.upload, 'media_gpt')
        if not os.path.exists(media_gpt_video):
            logger.info(f'文件夹不存在: {media_gpt_video}')
            continue

        video = [os.path.join(media_gpt_video, i) for i in os.listdir(media_gpt_video) if get_media_type(i) == MediaType.VIDEO]
        if len(video) == 0:
            continue
        parsed_data = media_gpt.prepare_video(VIDEO_PROMPT, video[0], ResponseModel)
        metadata = {
            '标题': parsed_data.title,
            '描述': parsed_data.description,
            '标签': tuple(parsed_data.keywords),
            '地点': '上海',
            '音乐': '热歌榜',
            '贴纸': '精选好房',
            '允许保存': '否',
        }
        await media_gpt.save_to_dy(metadata)


if __name__ == '__main__':
    download_media()      # 只需要运行1次
    asyncio.run(get_media_gpt_image())
    asyncio.run(get_media_gpt_video())
