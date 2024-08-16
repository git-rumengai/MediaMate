import asyncio
import json
import cv2
import httpx
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.const import HTTP_BIN, DEFAULT_REPLY
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


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


async def message_reply(prompt: str, messages: List[Dict[str, str]], chat_api: Optional[BaseMarket] = None) -> str:
    """监听后处理"""
    if chat_api:
        message_str = json.dumps(messages, indent=4)
        prompt += f'\n###\n{message_str}###\n'
        reply = chat_api.get_response(prompt)
    else:
        reply = prompt if prompt else DEFAULT_REPLY
    # 抖音评论有换行符会直接确认
    return reply.replace('\n', '   ')


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
