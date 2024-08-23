import asyncio

from mediamate.utils.log_manager import log_manager
from mediamate.agents.simple.photo_gpt import PhotoGPT


logger = log_manager.get_logger(__file__)


PROMPT = """
你是一名动物摄影师，你的工作是为小猫拍摄照片，现在，请告诉我你想拍摄一张什么内容的照片，包括场景、背景、艺术风格、照相机视角，模特穿着表情发型等各种细节。
使用绘画专业术语，不超过100字。
"""


async def get_photo():
    prompt = PROMPT
    photo_gpt = PhotoGPT()

    # 发表图文的标题, 标签和地点
    metadata = {
        '标题': '随手设计个吉祥物',
        '描述': '通过AI自动生成宠物图片并上传',
        '标签': ('宠物', '摄影', 'Agent'),
        '地点': '上海',
        '音乐': '热歌榜',
        '贴纸': '宠物',
        '允许保存': '否',
    }

    await photo_gpt.save_to_xhs(metadata, prompt, 3)
    await photo_gpt.save_to_dy(metadata, prompt, 3)


if __name__ == '__main__':
    asyncio.run(get_photo())
