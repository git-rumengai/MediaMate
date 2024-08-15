from fake_useragent import UserAgent
from typing import Optional
import io
from playwright.async_api import Page
from PIL import Image

from mediamate.tools.proxy import proxy_pool
from mediamate.config import config
from mediamate.utils.log_manager import log_manager
from mediamate.utils.enums import MediaType



logger = log_manager.get_logger(__file__)


async def get_random_proxy() -> str:
    """
    使用代理优先级:
    1. 代理池
    2. 静态ip
    3. 不用代理
    """
    proxy = config.get('FIXED_PROXY', '')
    if config.get('PROXY_NAME'):
        proxy = await proxy_pool.get_random_proxy()
    return proxy


async def get_direct_proxy() -> str:
    """
    使用代理优先级:
    1. 代理池
    2. 静态ip
    3. 不用代理
    """
    proxy = config.get('FIXED_PROXY', '')
    if config.get('PROXY_NAME'):
        proxy = await proxy_pool.get_direct_proxy()
    return proxy


def proxy_to_playwright(proxy: str) -> Optional[dict]:
    result = None
    if proxy:
        user, server = proxy.split('//')[1].split('@')
        username, password = user.split(':')
        result = {"server": f'http://{server}', "username": username, "password": password,}
    return result


def get_useragent(pc: bool = True):
    """  """
    pf = 'pc' if pc else 'mobile'
    user_agent = UserAgent(browsers='chrome', os='windows', platforms=pf)
    return user_agent.chrome

def get_media_type(filename: str) -> MediaType:
    """  """
    # 定义常见的文本文件扩展名
    text_extensions = {'txt', 'doc', 'docx', 'pdf', 'md', 'rtf', 'html', 'htm', 'xml', 'csv'}
    # 定义常见的语音文件扩展名
    audio_extensions = {'mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg', 'wma'}
    # 定义常见的视频文件扩展名
    video_extensions = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'mpeg', 'mpg', '3gp', 'webm'}
    # 定义常见的图片文件扩展名
    image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg', 'webp'}

    # 获取文件的扩展名
    file_extension = filename.split('.')[-1].lower()

    if file_extension in text_extensions:
        return MediaType.TEXT
    elif file_extension in audio_extensions:
        return MediaType.AUDIO
    elif file_extension in video_extensions:
        return MediaType.VIDEO
    elif file_extension in image_extensions:
        return MediaType.IMAGE
    else:
        return MediaType.UNKNOW


async def screenshot(page: Page, output_image_path: str):
    """ 保存屏幕截图 """
    image = await page.screenshot(full_page=True)
    with Image.open(io.BytesIO(image)) as img:
        img.save(output_image_path)



if __name__ == '__main__':
    result = get_useragent()
    print(result)
