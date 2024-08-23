import cv2
from abc import abstractmethod
import numpy as np
from typing import List, Tuple
from playwright.async_api import Locator

from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


class BaseVerify:
    def generate_bezier_path(self, start_pos, end_pos, steps=10):
        """
        生成二次贝塞尔曲线路径
        :param start_pos: 起点 (x, y)
        :param end_pos: 终点 (x, y)
        :param steps: 路径点数
        :return: 路径点列表 [(x1, y1), (x2, y2), ...]
        """
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = start_pos[1] + (end_pos[1] - start_pos[1]) * 0.3  # 调整 y 值以生成曲线效果

        t = np.linspace(0, 1, steps)
        path = []
        for i in t:
            x = (1 - i) ** 2 * start_pos[0] + 2 * (1 - i) * i * mid_x + i ** 2 * end_pos[0]
            y = (1 - i) ** 2 * start_pos[1] + 2 * (1 - i) * i * mid_y + i ** 2 * end_pos[1]
            path.append((x, y))
        return path

    async def get_element_position(self, element: Locator) -> Tuple[float, float]:
        """
        Get the position of the element identified by the locator.

        :param page: The Playwright page object
        :param locator: The CSS selector for the element
        :return: (x, y) coordinates of the element's position
        """
        if not await element.is_visible():
            raise ValueError("Element not found")

        bounding_box = await element.bounding_box()
        if not bounding_box:
            raise ValueError("Bounding box not found")

        x = bounding_box['x'] + bounding_box['width'] / 2
        y = bounding_box['y'] + bounding_box['height'] / 2
        return (x, y)

    async def calculate_path(self, locator: Locator, distance: float) -> List[Tuple[float, float]]:
        """
        Calculate the path for dragging the slider from its initial position to a target position.

        :param page: The Playwright page object
        :param locator: The CSS selector for the slider element
        :param distance: The distance to move the slider (in pixels)
        :return: List of (x, y) coordinates for the dragging path
        """
        start_pos = await self.get_element_position(locator)
        end_pos = (start_pos[0] + distance, start_pos[1])  # Assuming horizontal movement
        path = self.generate_bezier_path(start_pos, end_pos)
        return path

    @abstractmethod
    def calculate(self, *args, **kwargs):
        """ """


class MoveVerify(BaseVerify):
    def calculate(self, background_image_path, gap_image_path, matched_path: str = ''):
        """  """
        logger.info('处理平移验证码')
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


class RotateVerify(BaseVerify):
    def calculate(self, background_image_path, gap_image_path, matched_path: str = ''):
        """  """
        logger.info('处理旋转验证码')
        # 加载背景图和前景图
        background_img = cv2.imread(background_image_path)
        foreground_img = cv2.imread(gap_image_path)

        # 将图像转换为灰度图
        gray_bg = cv2.cvtColor(background_img, cv2.COLOR_BGR2GRAY)
        gray_fg = cv2.cvtColor(foreground_img, cv2.COLOR_BGR2GRAY)

        # 使用Canny边缘检测
        edges_bg = cv2.Canny(gray_bg, 50, 150)
        edges_fg = cv2.Canny(gray_fg, 50, 150)

        # 查找轮廓
        contours_bg, _ = cv2.findContours(edges_bg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_fg, _ = cv2.findContours(edges_fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 假设最大的轮廓是目标轮廓
        cnt_bg = max(contours_bg, key=cv2.contourArea)
        cnt_fg = max(contours_fg, key=cv2.contourArea)

        # 获取前景图轮廓的最小外接矩形
        rect_fg = cv2.minAreaRect(cnt_fg)

        # 设置初始值和步长
        best_angle = 0
        best_score = -1
        best_rotated_fg = None

        # 遍历可能的旋转角度，找到最佳匹配
        for angle in range(-90, 90, 1):  # 细粒度旋转，步长为1度
            # 旋转前景图像
            M = cv2.getRotationMatrix2D(rect_fg[0], angle, 1.0)
            rotated_fg = cv2.warpAffine(foreground_img, M, (foreground_img.shape[1], foreground_img.shape[0]))

            # 进行模板匹配
            result = cv2.matchTemplate(background_img, rotated_fg, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            # 找到最佳匹配角度
            if max_val > best_score:
                best_score = max_val
                best_angle = angle
                best_rotated_fg = rotated_fg

        # 输出最佳匹配角度和匹配得分
        logger.info(f"最佳角度: {best_angle} degrees, 分数: {best_score}")
        # 获取背景图像的宽度
        bg_width = background_img.shape[1]
        # 计算按钮平移量（以像素为单位）
        button_position = (best_angle / 360) * bg_width

        # 保存最佳匹配的旋转图像
        if matched_path:
            cv2.imwrite(matched_path, best_rotated_fg)
            logger.info(f"结果已保存 {matched_path}")
        return button_position

