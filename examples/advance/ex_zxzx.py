import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
import json
import sys

from mediamate.agents.advance.news_template_zxzx import NewsTemplateZxzx


script_params = sys.argv[1] if len(sys.argv) == 2 else '{}'
script_params = json.loads(script_params)


async def get_image_news():
    """  """
    # 制作新闻的参数
    news_params = {
        'title': script_params.get('title') or '最新资讯',
        'username': script_params.get('username') or 'RuMengAI',
        'topic': script_params.get('topic') or 'AIGC',
        'keywords': script_params.get('news_keywords') or ['人工智能', '苹果公司', '英伟达'],
        'qr_code': script_params.get('qr_code') or 'https://p3-pc.douyinpic.com/img/aweme-avatar/tos-cn-avt-0015_4fd936afe1c88ada2378c0cb12d251dc~c5_300x300.jpeg',
        'blacklist': script_params.get('blacklist', ()),
        'limit': script_params.get('limit', 6),
        'days': script_params.get('days', 7)
    }

    # 发布图文时的参数配置: 发布标题, 描述, 标签, 地点
    metadata = script_params.get('metadata') or {
        '标题': '科技新闻',
        '描述': '通过AI自动生成新闻并上传',
        '标签': ('RuMengAI', '新闻', '科技'),
        '地点': '上海',
        '音乐': '热歌榜',
        '贴纸': '科技',
        '允许保存': '否',
    }
    ntz = NewsTemplateZxzx()
    html_content = await ntz.get_html(**news_params)
    await ntz.save_to_xhs(html_content, metadata)
    await ntz.save_to_dy(html_content, metadata)


if __name__ == '__main__':
    asyncio.run(get_image_news())
