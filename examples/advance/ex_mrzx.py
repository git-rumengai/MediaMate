import sys
import os
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    sys.path.append(pythonpath)

import asyncio
import json
import requests
from lxml import etree
import sys
from mediamate.utils.common import get_useragent

from mediamate.agents.advance.news_template_mrzx import NewsTemplateMrzx


script_params = sys.argv[1] if len(sys.argv) == 2 else '{}'
script_params = json.loads(script_params)


# 如有必要禁用SSL
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

def get_data_img():
    """  """
    base_url = 'https://www.cneeex.com'
    start_url = f'{base_url}/qgtpfqjy/mrgk/2024n/'

    useragent = get_useragent()
    response = requests.get(start_url, headers={'User-Agent': useragent})
    html = etree.HTML(response.content)

    # html_string = etree.tostring(html, pretty_print=True, method="html", encoding="unicode")
    # print(html_string)

    target_tag = html.xpath('//ul[@class="list-unstyled articel-list"]/li[1]/a')
    link = f"{base_url}{target_tag[0].get('href')}"
    response = requests.get(link, headers={'User-Agent': useragent})
    html = etree.HTML(response.content)
    target_tag = html.xpath('//p[@style="text-align:center;"]/a')
    image_url = f"{base_url}{target_tag[0].get('href')}"
    return image_url


async def get_image_news():
    """  """
    # 制作新闻的参数
    news_params = {
        'title': {
            'title1': script_params.get('title1') or '正负极：',
            'title2': script_params.get('title2') or 'AI·碳中和',
            'title3': script_params.get('title3') or '每日资讯',
            'title4': script_params.get('title4') or 'BREAKING NEWS',
            'title5': script_params.get('title5') or 'AI·ESG'
        },
        'news_keywords': script_params.get('news_keywords') or {
            '碳中和': ['碳中和', '节能减排'],
            '人工智能': ['AI', 'AIGC'],
            '科技新闻': ['人工智能', '苹果公司', '英伟达']
        },
        'qr_code': script_params.get('qr_code') or 'https://p3-pc.douyinpic.com/img/aweme-avatar/tos-cn-avt-0015_4fd936afe1c88ada2378c0cb12d251dc~c5_300x300.jpeg',
        'data_imag': script_params.get('data_imag') or get_data_img(),
        'blacklist': script_params.get('blacklist', ()),
        'limit': script_params.get('limit', 6),
        'days': script_params.get('days', 7),
        'truncat': True,
        'sentence': script_params.get('sentence', 2),
    }

    # 发布图文时的参数配置: 发布标题, 描述, 标签, 地点
    metadata = script_params.get('metadata') or {
        '标题': '财经新闻',
        '描述': '通过AI自动生成新闻并上传',
        '标签': ('量化私募', 'A股', '龙虎榜'),
        '地点': '上海',
        '音乐': '热歌榜',
        '贴纸': '财经新闻',
        '允许保存': '否',
    }
    ntz = NewsTemplateMrzx()
    html_content = await ntz.get_html(**news_params)
    await ntz.save_to_xhs(html_content, metadata)
    await ntz.save_to_dy(html_content, metadata)


if __name__ == '__main__':
    # get_data_img()
    asyncio.run(get_image_news())
