import asyncio
import os
import requests
from pydantic import BaseModel, Field, constr, field_validator
from typing import List
from mediamate.agents.simple.media_gpt import MediaGPT
from mediamate.utils.log_manager import log_manager
from mediamate.config import config
from mediamate.utils.llm_pydantic import parse_response
from mediamate.utils.functions import get_media_type
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

按照如下schemas描述输出JSON格式：
{ResponseModel.model_json_schema()}

图片描述：
"""

VIDEO_PROMPT = f"""
根据这个视频内容帮我生成一篇主题为"精选好房"的抖音风格文案。

按照如下schemas描述输出JSON格式：
{ResponseModel.model_json_schema()}

视频描述：
"""

IMAGES = [
    'https://ss2.meipian.me/users/2531394/8b3ab230-4016-11eb-a090-d76407546a82.jpg',
    'https://p3.toutiaoimg.com/origin/pgc-image/303f5bc0b48249f094c2f7f5d4ae3a04?from=pc'
]

VIDEO = 'https://www.douyin.com/aweme/v1/play/?file_id=d35918c6c3554907982cb23c6a9d8059&is_play_url=1&line=0&sign=6c432f512bbc4e0fa7a420cf1a8d6fa3&source=PackSourceEnum_PUBLISH&uifid=3c3e9d4a635845249e00419877a3730e2149197a63ddb1d8525033ea2b3354c2fcb74766499cf3c6f79cb8aaebb8ad2f238d9adf46a107ca2cab64707cde3df42bbe0ddf12d441dcd90a0b8277bb88cf9e8e238a05cdb6085c040435f1bde20f7b466e80aa73aecfc457e3d188b457bcf2ea3af492b50f2cebfa4fc6dc1381a91632e2ce795d99aa474d7ce90f615e1189052baa9b1af5df6f12fb2b62740db6&video_id=v0200fg10000cqpn837og65jf3ve9fbg&aid=6383'


def download_media():
    """ 下载示例内容, 组图保存到xhs, 视频保存到dy """
    media_config = config.MEDIA.get('media')
    if media_config:
        for index, image_url in enumerate(IMAGES):
            response = requests.get(image_url, timeout=30)
            for xhs in media_config.get('xhs', []):
                account = xhs['account']
                platform = xhs['platform']
                account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/media_gpt_images'
                os.makedirs(account_dir, exist_ok=True)
                with open(f'{account_dir}/{index}.jpg', 'wb') as file:
                    file.write(response.content)
                break

        response = requests.get(VIDEO, timeout=60)
        for dy in media_config.get('dy', []):
            account = dy['account']
            platform = dy['platform']
            account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/media_gpt_video'
            os.makedirs(account_dir, exist_ok=True)
            with open(f'{account_dir}/1.mp4', 'wb') as file:
                file.write(response.content)
            break


async def get_media_gpt():
    """  """
    media_gpt = MediaGPT()
    parsed_data: ResponseModel
    media_config = config.MEDIA.get('media')
    if media_config:
        media_gpt.init(IMAGES_PROMPT)
        for xhs in media_config.get('xhs', []):
            account = xhs['account']
            platform = xhs['platform']
            account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/media_gpt_images'
            if not os.path.exists(account_dir):
                logger.info(f'文件夹不存在: {account_dir}')
                continue

            images = [os.path.join(account_dir, i) for i in os.listdir(account_dir) if get_media_type(i) == MediaType.IMAGE]
            response = media_gpt.prepare_image(images)
            flag, parsed_data = parse_response(response, ResponseModel)
            if not flag:
                logger.info('llm解析结果出错, 请检查提示词或者代码逻辑')
                continue

            # 发表图文的标题, 标签和地点
            media_title = parsed_data.title
            media_desc = parsed_data.description
            media_labels = tuple(parsed_data.keywords)
            media_location = '上海'
            # 上传图片时最长等待时间
            media_wait_minute = 3
            media_gpt.init_media(media_title, media_desc, media_labels, media_location, media_wait_minute)
            await media_gpt.save_to_xhs(account_dir)

        media_gpt.init(VIDEO_PROMPT)
        for dy in media_config.get('dy', []):
            account = dy['account']
            platform = dy['platform']
            account_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/media_gpt_video'
            if not os.path.exists(account_dir):
                logger.info(f'文件夹不存在: {account_dir}')
                continue


            video = [os.path.join(account_dir, i) for i in os.listdir(account_dir) if get_media_type(i) == MediaType.VIDEO]
            if len(video) == 0:
                continue
            response = media_gpt.prepare_video(video[0])
            flag, parsed_data = parse_response(response, ResponseModel)
            if not flag:
                logger.info('llm解析结果出错, 请检查提示词或者代码逻辑')
                continue

            # 发表图文的标题, 标签和地点
            media_title = parsed_data.title
            media_desc = parsed_data.description
            media_labels = tuple(parsed_data.keywords)
            media_location = '上海'
            # 上传图片时最长等待时间
            media_wait_minute = 3
            # 发布抖音参数: 贴纸, 是否允许保存
            media_theme = '精选好房'
            media_download = '否'
            media_gpt.init_media(media_title, media_desc, media_labels, media_location, media_wait_minute, media_theme, media_download)
            await media_gpt.save_to_dy(account_dir)


if __name__ == '__main__':
    # download_media()      # 只需要运行1次
    asyncio.run(get_media_gpt())
