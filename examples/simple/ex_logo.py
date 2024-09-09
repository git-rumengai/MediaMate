import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
import random

from mediamate.utils.log_manager import log_manager
from mediamate.agents.simple.logo_gpt import LogoGPT


logger = log_manager.get_logger(__file__)


LOGO_PROMPT = [
    'flat ios app icon for chatbot, minimalist, baby blue and white.',
    'squared with round edges mobile app logo design, flat vector app icon of a classic sculpture of a beautiful goddess posing and taking a selfie, white background.',
    'restaurant app line icons, no background, modern, minimalistic, no color, realistic.',
    'Gear icon with a cloud in the middle for a app icon in blue color.',
    'food delivery app icon, 3d, orange color.',
    'Outline icon set of technology, black line, minimal, white background, ui, ux, design, app, clean fresh design.',
    'Outline icon set of financial industry, black line, with yellow highlight, minimal, white background, UI, UX, design, app, clean fresh design.',
    'Outline icon set of medical, frosted glass icon set, colorful, neon light, dark background.',
    'A 3D icon, shopping cart, isometric, gradient glass, colorful color matching, plain background, 3D rendering, C4D, blender.',
    'A icon of an mail, frosted glass texture, glossy base, isometric, translucent, gradient colour of green and yellow, technology sense, studio lighting, plain background, 3D rendering, C4D, blender.',
    '3D Icon Set of food and beverage industry,plain background, isometric, translucent, 3D rendering, C4D, blender.'
 ]


async def get_logo(number: int = 1):
    mascot_gpt = LogoGPT()
    # 发布图文时的参数配置: 发布标题, 描述, 标签, 地点
    metadata = {
        '标题': '随手设计个吉祥物',
        '描述': '通过AI自动生成吉祥物并上传',
        '标签': ('吉祥物', 'AI', 'Agent'),
        '地点': '上海',
        '音乐': '热歌榜',
        '贴纸': '吉祥物',
        '允许保存': '否',
    }
    prompts = [random.choice(LOGO_PROMPT) for _ in range(number)]
    await mascot_gpt.save_to_xhs(metadata, prompts)
    await mascot_gpt.save_to_dy(metadata, prompts)


if __name__ == '__main__':
    asyncio.run(get_logo(3))
