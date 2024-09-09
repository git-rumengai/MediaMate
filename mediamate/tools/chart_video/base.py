from abc import abstractmethod
import os.path
from typing import Tuple
import random
import requests
import base64
from PIL import Image
from io import BytesIO

from moviepy.editor import ImageSequenceClip, ImageClip, concatenate_videoclips

from mediamate.utils.enums import VideoOrientation, Resolution
from mediamate.config import ConfigManager
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__name__)


class BaseChat:
    def __init__(self, data_path: str = ''):
        self.data_path = data_path
        metafilename = os.path.join(data_path, 'metadata.yaml')
        self.metadata = ConfigManager(metafilename)
        self.chart_video_config = self.metadata.get('chart_video')
        self.filename = os.path.join(data_path, self.chart_video_config.get('filename'))
        video_mode = self.chart_video_config.get('orientation', VideoOrientation.LANDSCAPE.value)
        resolution = self.chart_video_config.get('resolution', Resolution.ULTRA_HD.value)
        self.width, self.height = self.get_dimensions(video_mode, resolution)

    @abstractmethod
    def generate_frames(self):
        """  """

    def get_dimensions(self, video_mode: Tuple[int, int], resolution: Tuple[int, int]):
        """
        根据视频模式和分辨率获取宽度和高度。

        :param video_mode: 视频模式，使用 VideoOrientation 枚举
        :param resolution: 分辨率，使用 Resolution 枚举
        :return: 宽度和高度的元组
        """
        width, height = resolution
        aspect_ratio_width, aspect_ratio_height = video_mode

        # 计算宽高
        if aspect_ratio_width / aspect_ratio_height > width / height:
            # 宽高比偏宽，调整宽度
            new_width = width
            new_height = int(width * aspect_ratio_height / aspect_ratio_width)
        else:
            # 宽高比偏高，调整高度
            new_height = height
            new_width = int(height * aspect_ratio_width / aspect_ratio_height)
        return new_width, new_height

    def generate_ui_avatar(self, word, size=128, background_color=None, font_color=None, save_path=None):
        """
        Generate an avatar using UI Avatars service.
        """
        def get_luminance(color):
            """Calculate the luminance of a given color."""
            rgb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

        def get_contrast_ratio(color1, color2):
            """Calculate the contrast ratio between two colors."""
            lum1 = get_luminance(color1)
            lum2 = get_luminance(color2)
            return (max(lum1, lum2) + 0.05) / (min(lum1, lum2) + 0.05)

        def generate_color_combination(bg=None, fc=None):
            """Generate a color combination with sufficient contrast."""
            while True:
                background_color = bg if bg else '{:06x}'.format(random.SystemRandom().randint(0, 0xFFFFFF))
                font_color = fc if fc else '{:06x}'.format(random.SystemRandom().randint(0, 0xFFFFFF))
                contrast_ratio = get_contrast_ratio(background_color, font_color)
                if contrast_ratio >= 4.5:  # WCAG AA standard for contrast ratio
                    # 确保背景色较暗，字体颜色较亮
                    if get_luminance(background_color) > get_luminance(font_color):
                        return background_color, font_color
        # 生成有反差的背景和前景色
        if background_color and font_color:
            bg, fc = background_color, font_color
        else:
            bg, fc = generate_color_combination(background_color, font_color)

        url = f"https://ui-avatars.com/api/?name={word}&size={size}&background={bg}&color={fc}&rounded=true"
        response = requests.get(url)

        if response.status_code == 200:
            avatar_image = Image.open(BytesIO(response.content))
            if save_path:
                avatar_image.save(save_path)
                logger.info(f"Avatar saved to {save_path}")
            return avatar_image
        else:
            logger.info(f"Failed to retrieve avatar. Status code: {response.status_code}")
            return None

    def pil_image_to_base64(self, image) -> str:
        """ 将PIL图像对象转换为Base64编码的字符串。 """
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    def create_video(self):
        """  """
        frame_folder = os.path.join(self.data_path, 'frames')
        if not os.path.exists(frame_folder) or len(os.listdir(frame_folder)) == 0:
            logger.info('图片文件不存在, 先生成图片')
            self.generate_frames()
        frame_files = [os.path.join(frame_folder, f) for f in sorted(os.listdir(frame_folder)) if f.endswith('.png')]
        filename = self.chart_video_config.get('filename').rsplit('.')[0]
        output_file = os.path.join(self.data_path, f'{filename}.mp4')

        # 创建Clip对象
        fps = self.chart_video_config.get('fps')
        first_frame_clip = ImageClip(frame_files[0]).set_duration(3)
        last_frame_clip = ImageClip(frame_files[-1]).set_duration(3)
        middle_clip = ImageSequenceClip(frame_files, fps=fps)

        # 拼接Clip对象
        final_clip = concatenate_videoclips([first_frame_clip, middle_clip, last_frame_clip])

        # 输出视频文件
        final_clip.write_videofile(output_file, codec="libx264")
        return output_file


if __name__ == '__main__':
    # from mediamate.tools.chart_video.charts.bar_race import BarRace
    # data_path = r'C:\Users\Admin\Desktop\MediaMate\data\upload\xiaohongshu\RuMengAI\bar_race'
    # cv = BarRace(data_path).create_video()

    from mediamate.tools.chart_video.charts.line_trend import LineTrend

    data_path = r'C:\Users\Admin\Desktop\MediaMate\data\upload\xiaohongshu\RuMengAI\line_trend'
    cv = LineTrend(data_path).create_video()
