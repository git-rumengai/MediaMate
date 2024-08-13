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


def generate_human_path(start, end, steps=10):
    # 生成一个平滑且不规则的路径
    points = [np.array([start, 0])]
    for i in range(1, steps):
        t = i / steps
        offset = np.random.uniform(-10, 10)  # 随机偏移
        x = start + t * (end - start) + offset
        points.append(np.array([x, 0]))
    points.append(np.array([end, 0]))
    return points


async def calculate_gap_position(background_image_path, gap_image_path, matched_path: str = ''):
    # 读取背景图和缺口图
    background_image = cv2.imread(background_image_path, 0)
    gap_image = cv2.imread(gap_image_path, 0)
    raw_bg_image = background_image
    raw_gap_image = gap_image

    # 图像预处理：调整亮度和对比度
    alpha = 1.5  # 对比度增益
    beta = 30  # 亮度增益
    background_image = cv2.convertScaleAbs(background_image, alpha=alpha, beta=beta)
    gap_image = cv2.convertScaleAbs(gap_image, alpha=alpha, beta=beta)

    # 图像预处理：边缘检测
    background_image = cv2.Canny(background_image, 100, 200)
    gap_image = cv2.Canny(gap_image, 100, 200)

    # 使用模板匹配找到缺口位置
    result = cv2.matchTemplate(background_image, gap_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 缺口位置
    gap_position = max_loc[0]

    # 视觉验证：在背景图上绘制矩形框
    if matched_path:
        h, w = raw_gap_image.shape
        cv2.rectangle(raw_bg_image, max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 0, 255), 2)
        cv2.imwrite(matched_path, raw_bg_image)
    return gap_position


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
    return reply
