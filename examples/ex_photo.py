import asyncio

from mediamate.utils.log_manager import log_manager
from mediamate.agents.simple.photo_gpt import PhotoGPT


logger = log_manager.get_logger(__file__)


PROMPT = """
你是一名摄影师，你的工作是为各种模特拍摄照片，现在，请告诉我你想拍摄一张什么内容的照片，包括场景、背景、艺术风格、照相机视角，模特穿着表情发型等各种细节。
表述尽量简洁，使用结构化语言。回复请以"这个美女..."开头
"""

async def get_photo():
    prompt = PROMPT
    photo_gpt = PhotoGPT()
    photo_gpt.init(prompt)

    # 发表图文的标题, 标签和地点
    media_title = '发现生活的美'
    media_labels = ('RuMengAI', '模特', '摄影')
    media_location = '上海'
    # 上传图片时最长等待时间
    media_wait_minute = 3
    # 发布抖音参数: 贴纸, 是否允许保存
    media_theme = '模特'
    media_download = '否'
    photo_gpt.init_media(media_title, media_labels, media_location, media_theme, media_wait_minute, media_download)


    await photo_gpt.save_to_xhs()
    await photo_gpt.save_to_dy()


if __name__ == '__main__':
    asyncio.run(get_photo())
