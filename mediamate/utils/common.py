from fake_useragent import UserAgent
from typing import Optional
import io
from playwright.async_api import Page
from PIL import Image
import asyncio
import json
import re
import httpx
from typing import List, Dict

from datetime import datetime

from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.const import HTTP_BIN
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


async def get_httpbin(proxy: str) -> str:
    """  """
    for i in range(3):
        try:
            async with httpx.AsyncClient(proxies={'http://': proxy, 'https://': proxy}) as client:
                response = await client.get(HTTP_BIN)
                response.raise_for_status()  # 如果响应码不是 200，会抛出异常
                if response.status_code == 502:
                    raise httpx.HTTPStatusError("502 Bad Gateway", request=response.request, response=response)
                pre_element_text = response.text.strip()
                if pre_element_text:
                    pre_element_text = json.loads(pre_element_text)
                else:
                    pre_element_text = {}
                return pre_element_text.get('origin')
        except httpx.HTTPStatusError as e:
            logger.info(f"failed: {e}")
            logger.info('重试获取ip')
        except httpx.RequestError as e:
            logger.info(f"failed: {e}")
            logger.info('重试获取ip')
        await asyncio.sleep(1)
    logger.info('重试3次无法获取IP, 忽略')
    return ''


def format_expiration_time(cookies):
    for cookie in cookies:
        expiration_time = cookie['expires']
        if isinstance(expiration_time, float):
            expiration_time = int(expiration_time)
        expiration_datetime = datetime.fromtimestamp(expiration_time)
        formatted_time = expiration_datetime.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Cookie '{cookie['name']}' 的过期时间: {formatted_time}")
    logger.info(f'Cookie数量: {len(cookies)}')


async def check_cookies_valid(cookies, identification: str) -> bool:
    """ 检查是否有登录表示或者登录信息是否过期 """
    if not cookies:
        return False
    current_time = datetime.now()
    # format_expiration_time(cookies)
    for cookie in cookies:
        if cookie.get('name') == identification:
            expiration_time = cookie['expires']
            if isinstance(expiration_time, float):
                expiration_time = int(expiration_time)
                expiration_datetime = datetime.fromtimestamp(expiration_time)
                formatted_time = expiration_datetime.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"Cookie '{cookie['name']}' 的过期时间: {formatted_time}")
                if expiration_datetime > current_time:
                    return True
    return False


async def handle_dialog_dismiss(dialog):
    """监听后处理"""
    await dialog.dismiss()


async def handle_dialog_accept(dialog):
    """监听后处理"""
    await dialog.accept()


async def message_reply(chat_api: BaseMarket, prompt: str, messages: List[Dict[str, str]]) -> str:
    """监听后处理"""
    message_str = json.dumps(messages, indent=4, ensure_ascii=False)
    prompt += f'\n###\n{message_str}###\n'
    logger.info(prompt)
    reply = chat_api.get_response(prompt)
    return reply


async def download_image(session, url: str, file_path: str):
    """异步下载图片并保存到文件"""
    async with session.get(url) as response:
        if response.status == 200:
            with open(file_path, 'wb') as file:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    file.write(chunk)
            logger.info(f'文件下载完毕: {file_path}')
        else:
            logger.info(f"Failed to download image, status code: {response.status}")


def extract_at_users(comment) -> list:
    """ 正则表达式匹配@某人 """
    pattern = r'@[\w]+'
    at_users = re.findall(pattern, comment)
    return at_users


def remove_at_users(comment) -> str:
    """ 删除 @某人 """
    pattern = r'@[\w]+'
    # 使用sub方法将匹配到的内容替换为空字符串
    cleaned_comment = re.sub(pattern, '', comment)
    return cleaned_comment


def extract_json(text: str) -> str:
    """ 从文本中提取 JSON 数据，支持任意类型的嵌套 JSON 对象和数组 """
    start = -1
    brace_count = 0
    bracket_count = 0
    in_quotes = False
    for i, char in enumerate(text):
        if char == '"' and (i == 0 or text[i - 1] != '\\'):  # 检查是否在引号内
            in_quotes = not in_quotes
        elif char == '{' and not in_quotes:  # 开始新的 JSON 对象
            if start == -1:
                start = i
            brace_count += 1
        elif char == '}' and not in_quotes:  # 结束一个 JSON 对象
            brace_count -= 1
            if brace_count == 0 and bracket_count == 0 and start != -1:
                json_str = text[start:i + 1]
                # 替换换行符为 \n
                json_str = json_str.replace('\n', '\\n')
                return json_str
        elif char == '[' and not in_quotes:  # 开始新的数组
            if start == -1:
                start = i
            bracket_count += 1
        elif char == ']' and not in_quotes:  # 结束一个数组
            bracket_count -= 1
            if brace_count == 0 and bracket_count == 0 and start != -1:
                json_str = text[start:i + 1]
                # 替换换行符为 \n
                json_str = json_str.replace('\n', '\\n')
                return json_str
    return ""


def add_message_to_list(new_msg: Dict[str, str], lst: List[Dict[str, str]]) -> List:
    if not any(set(new_msg.values()) & set(existing_dict.values()) for existing_dict in lst):
        lst.append(new_msg)
    return lst
