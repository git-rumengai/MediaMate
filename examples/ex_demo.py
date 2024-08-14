"""
该脚本用来初始化一个发表图文的demo
"""
import asyncio
import os
import requests
from mediamate.config import config, ConfigManager


async def get_photo():
    # 1. 下载一张图片
    url = 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo311jqpqj76k005p19khr4c4688pl4em8?imageView2/2/w/540/format/webp|imageMogr2/strip2'
    response = requests.get(url)

    # 2. 创建配置
    metadata = ConfigManager()

    media_config = config.MEDIA.get('media')
    if media_config:
        dy_config = media_config.get('dy', [])
        for i in dy_config:
            platform = i['platform']
            account = i['account']
            data_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/demo'
            os.makedirs(data_dir, exist_ok=True)
            with open(f'{data_dir}/rumengai.png', 'wb') as file:
                file.write(response.content)

            metadata.init(f'{data_dir}/metadata.yaml')
            await metadata.set('标题', '我为RuMengAI代言')
            await metadata.set('描述', '这只是个测试')
            await metadata.set('标签', ['AI社交'])
            await metadata.set('地点', '上海')
            await metadata.set('贴纸', 'AI')
            await metadata.set('允许保存', '否')

        xhs_config = media_config.get('xhs', [])
        for i in xhs_config:
            platform = i['platform']
            account = i['account']
            data_dir = f'{config.DATA_DIR}/upload/{platform}/{account}/demo'
            os.makedirs(data_dir, exist_ok=True)
            with open(f'{data_dir}/rumengai.png', 'wb') as file:
                file.write(response.content)

            metadata.init(f'{data_dir}/metadata.yaml')
            await metadata.set('标题', '自动上传作品，代码已经开源')
            await metadata.set('描述', 'GitHub已开源')
            await metadata.set('标签', ['AI社交'])
            await metadata.set('地点', '上海')


if __name__ == '__main__':
    asyncio.run(get_photo())
