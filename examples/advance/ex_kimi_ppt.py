import sys
import os
import glob
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
import json
import sys

from mediamate.config import config
from mediamate.agents.advance.kimi_ppt import KimiPPT
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)

script_params = sys.argv[1] if len(sys.argv) == 2 else '{}'
script_params = json.loads(script_params)


async def get_kimi_ppt(delete_ppt: bool = True):
    """  """
    ppt_dir = f'{config.DATA_DIR}/upload/kimi'
    os.makedirs(ppt_dir, exist_ok=True)
    ppt_path = f'{ppt_dir}/0.pptx'

    kimi_ppt_params = {
        'headless': script_params.get('headless') or False,
        'topic': script_params.get('topic') or 'AI文生图商业计划书',
        'logo_path': script_params.get('logo_path') or f'{os.path.dirname(config.PROJECT_DIR)}/docs/imgs/logo-透明底.png'.replace('\\', '/'),
        'username': script_params.get('username') or 'RuMengAI',
        'scene': script_params.get('scene') or '商业计划',
        'style': script_params.get('style') or '简约',
        'color_index': script_params.get('color_index') or -4,
        'card_index': script_params.get('card_index') or 0
    }
    # 发布图文时的参数配置: 发布标题, 描述, 标签, 地点
    metadata = script_params.get('metadata') or {
        '标题': 'XX涨粉操作手册',
        '描述': '通过AI自动生成操作手册并上传',
        '标签': ('涨粉', '教程', 'RuMengAI'),
        '地点': '上海',
        '音乐': '热歌榜',
        '贴纸': '手册',
        '允许保存': '否',
    }
    kppt = KimiPPT(ppt_path)
    await kppt.get_ppt(**kimi_ppt_params)
    await kppt.save_to_xhs(metadata)
    await kppt.save_to_dy(metadata)

    if delete_ppt:
        ppt_files = glob.glob(os.path.join(config.DATA_DIR, '*.ppt'))
        pptx_files = glob.glob(os.path.join(config.DATA_DIR, '*.pptx'))
        all_files = ppt_files + pptx_files
        for file_path in all_files:
            os.remove(file_path)


if __name__ == '__main__':
    asyncio.run(get_kimi_ppt(delete_ppt=False))
