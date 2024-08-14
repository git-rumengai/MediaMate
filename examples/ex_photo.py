import asyncio

from mediamate.utils.log_manager import log_manager
from mediamate.agents.simple.photo_gpt import PhotoGPT


logger = log_manager.get_logger(__file__)


# PROMPT = """
# 你是一名摄影师，你的工作是为各种模特拍摄照片，现在，请告诉我你想拍摄一张什么内容的照片，包括场景、背景、艺术风格、照相机视角，模特穿着表情发型等各种细节。
# 使用绘画专业术语，语言简洁，突出重点。
# """

PROMPT = """
你是一名动物摄影师，你的工作是为各种小宠物拍摄照片，现在，请告诉我你想拍摄一张什么内容的照片，包括场景、背景、艺术风格、照相机视角，模特穿着表情发型等各种细节。
使用绘画专业术语，语言简洁明了。
"""


async def get_photo():
    prompt = PROMPT
    photo_gpt = PhotoGPT()
    photo_gpt.init(prompt)

    # 发表图文的标题, 标签和地点
    media_title = '这是AI自动生成并上传的图片模板，你觉得怎么样呢？（代码已开源）'
    media_labels = ('RuMengAI', '宠物', '摄影')
    media_location = '上海'
    # 上传图片时最长等待时间
    media_wait_minute = 3
    # 发布抖音参数: 贴纸, 是否允许保存
    media_theme = '宠物'
    media_download = '否'
    photo_gpt.init_media(media_title, media_labels, media_location, media_theme, media_wait_minute, media_download)


    await photo_gpt.save_to_xhs()
    await photo_gpt.save_to_dy()


if __name__ == '__main__':
    asyncio.run(get_photo())
