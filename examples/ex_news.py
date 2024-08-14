import asyncio
from mediamate.agents.simple.image_newspaper import ImageNewspaper

"""
运行该脚本需要确保网络可以访问Google
"""

async def get_image_news():
    # 自动创建图片格式新闻
    # 新闻名称
    news_title = '科技新闻报'
    # 从Google新闻主题中搜索:
    # 主题列表: 'Top Stories', 'World', 'Nation', 'Business', 'Technology', 'Entertainment', 'Sports', 'Science','Health'
    news_topic = 'Technology'
    # 搜索关键词
    news_keywords = ('AI', 'AI图片', 'AI音乐', 'AI视频')

    # 发布图文时的参数配置
    # 发布标题, 描述, 标签, 地点
    media_title = '这是AI自动生成并上传的新闻模板，你觉得怎么样呢？（代码已开源）'
    media_desc = '科技新闻报道'
    media_labels = ('RuMengAI', '新闻', '科技')
    media_location = '上海'
    # 上传图片时最长等待时间
    media_wait_minute = 3
    # 发布抖音参数: 贴纸, 是否允许保存
    media_theme = '科技新闻'
    media_download = '否'

    inp = ImageNewspaper()
    inp.init(news_title, news_topic, news_keywords)
    inp.init_media(media_title, media_desc, media_labels, media_location, media_wait_minute, media_theme, media_download)

    await inp.get_md_news(limit=5, days=100)
    await inp.save_to_xhs()
    await inp.save_to_dy()


if __name__ == '__main__':
    asyncio.run(get_image_news())
