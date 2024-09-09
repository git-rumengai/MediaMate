import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
from mediamate.agents.simple.image_newspaper import ImageNewspaper

# 如有必要禁用SSL
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


async def get_image_news():
    news_title = '财经新闻'
    # news_keywords = ('AI图片', 'AI音乐', 'AI视频', 'AI搜索')
    news_keywords = ('量化私募', 'A股', '龙虎榜')

    # 发布图文时的参数配置: 发布标题, 描述, 标签, 地点
    metadata = {
        '标题': news_title,
        '描述': '通过AI自动生成新闻并上传',
        '标签': news_keywords,
        '地点': '上海',
        '音乐': '热歌榜',
        '贴纸': '财经新闻',
        '允许保存': '否',
    }
    inp = ImageNewspaper(metadata['标题'], news_keywords)
    await inp.save_to_xhs(metadata)
    await inp.save_to_dy(metadata)


if __name__ == '__main__':
    asyncio.run(get_image_news())
