import asyncio
import random

from mediamate.utils.log_manager import log_manager
from mediamate.agents.simple.mascot_gpt import MascotGPT


logger = log_manager.get_logger(__file__)


PROMPT = """
作为一名吉祥物设计师，您的主要职责是为我提供设计吉祥物的灵感。
品牌：{brand}
我希望的风格是：{style}
背景颜色是：{bg_color}
请给出您的设计方案，使用绘画专业术语，语言简洁明了。输出结果以“这是我为{brand}设计的吉祥物\n...”开头。
"""

BRANDS = ['华为', '小米', '阿里巴巴', '腾讯', '百度', '美团', '京东', '字节跳动', 'VIVO', 'OPPO', '联想', '格力',
          '美的', '海尔', '蒙牛', '伊利', '五粮液', '茅台', '苹果', '微软', '谷歌', '亚马逊', 'Facebook', '耐克',
          '可口可乐', "麦当劳", '宝马', '梅赛德斯-奔驰', '路易威登', '古驰', '普拉达', '香奈儿', '爱马仕', '迪士尼',
          'Netflix', '三星', '丰田', '本田', '大众', '保时捷', '法拉利', '兰博基尼']
STYLES = ['极简主义', '未来主义', '复古', '复古风格', '手绘', '艺术', '环保', '自然', '奢华', '优雅', '大胆', '多彩',
          '几何', '抽象', '文化', '民族', '运动', '运动型', '吉祥物', '科技', '数字']
BG_COLOR = ['白色', '黑色', '红色', '蓝色', '绿色', '黄色', '紫色', '粉色', '橙色', '棕色', '灰色', '金色', '银色',
            '米色', '海军蓝', '蓝绿色', '青柠', '品红', '绿松石', '橄榄', '珊瑚', '水', '薰衣草']


async def get_mascot(seed: int=1):
    random.seed(seed)
    brand = random.choice(BRANDS)
    style = random.choice(STYLES)
    bg_color = random.choice(BG_COLOR)
    prompt = PROMPT.format(
        brand=brand,
        style=style,
        bg_color=bg_color
    )

    mascot_gpt = MascotGPT()
    mascot_gpt.init(prompt)
    # 发表图文的标题, 标签和地点
    media_title = f'这是利用AI自动生成并上传的图文模板，你觉得怎么样呢？（代码已开源）'
    media_labels = ('RuMengAI', '吉祥物', '科技', brand)
    media_location = '上海'
    # 上传图片时最长等待时间
    media_wait_minute = 3
    # 发布抖音参数: 贴纸, 是否允许保存
    media_theme = '吉祥物'
    media_download = '否'
    mascot_gpt.init_media(media_title, media_labels, media_location, media_wait_minute, media_theme, media_download)


    await mascot_gpt.save_to_xhs()
    await mascot_gpt.save_to_dy()


if __name__ == '__main__':
    asyncio.run(get_mascot())
