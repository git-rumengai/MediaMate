import subprocess
import requests
import os
import base64
from typing import Optional
from mimetypes import guess_type

from mediamate.utils.common import get_media_type
from mediamate.utils.enums import MediaType
from mediamate.utils.log_manager import log_manager
from mediamate.tools.api_market.recognizer import OpenAIImageRecognizer, OpenAIAudioRecognizer


logger = log_manager.get_logger(__file__)


class ConvertToText:
    """ 将图片/语音/视频转为文本 """
    def __init__(self, image_recognizer: Optional[OpenAIImageRecognizer] = None, audio_recognizer: Optional[OpenAIAudioRecognizer] = None):
        self.image_recognizer: OpenAIImageRecognizer = image_recognizer
        self.audio_recognizer: OpenAIAudioRecognizer = audio_recognizer

    def read_file(self, filename: str) -> str:
        """  """
        file_type = get_media_type(filename)
        if file_type == MediaType.TEXT:
            text = self.read_text_file(filename)
        elif file_type == MediaType.IMAGE:
            text = self.read_image_file(filename)
        elif file_type == MediaType.AUDIO:
            text = self.read_audio_file(filename)
        elif file_type == MediaType.VIDEO:
            text = self.read_video_file(filename)
        else:
            raise ValueError('未知文件类型, 无法处理')
        return text

    def read_url(self, url: str, file_type: str) -> str:
        """ 从url中直接识别内容 """
        if file_type.lower() == MediaType.IMAGE.value:
            text = self.read_image_file(url)
        elif file_type.lower() == MediaType.AUDIO.value:
            # text = self.read_audio_file(url)
            raise ValueError('暂不支持')
        elif file_type.lower() == MediaType.VIDEO.value:
            # text = self.read_video_file(url)
            raise ValueError('暂不支持')
        else:
            raise ValueError('未知文件类型, 无法处理')
        return text

    def read_text_file(self, filename: str) -> str:
        """  """
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            return f"读取文件时发生错误. {filename}, Error: {e}"

    def local_image_url(self, image_path):
        """  """
        mime_type, _ = guess_type(image_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        with open(image_path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{base64_encoded_data}"

    def read_image_file(self, filename: str) -> str:
        """  """
        try:
            if filename.startswith('http'):
                file_url = filename
            else:
                file_url = self.local_image_url(filename)
            response = self.image_recognizer.get_response(file_url)
            return response
        except Exception as e:
            return f"读取图片文件时发生错误. {filename}, Error: {e}"

    def read_audio_file(self, filename: str) -> str:
        """  """
        try:
            response = self.audio_recognizer.get_response(filename)
            return response
        except Exception as e:
            return f"读取音频文件时发生错误. {filename}, Error: {e}"

    def extract_audio_from_video(self, video_path):
        """ 从video提取audio """
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise RuntimeError("FFmpeg未安装或未添加到系统路径中。")

        video_dir, video_filename = os.path.split(video_path)
        video_basename, video_ext = os.path.splitext(video_filename)
        audio_output_path = os.path.join(video_dir, f"{video_basename}.wav")
        # 使用FFmpeg提取音频
        command = [
            'ffmpeg',
            '-y',               # 总是覆盖文件
            '-i', video_path,  # 输入视频文件
            '-vn',  # 禁用视频流
            '-acodec', 'pcm_s16le',  # 设置音频编码为PCM 16位小端
            '-ar', '44100',  # 设置采样率为44100 Hz
            '-ac', '2',  # 设置音频通道数为2（立体声）
            audio_output_path  # 输出音频文件路径
        ]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return audio_output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg执行失败: {e}")

    def read_video_file(self, filename: str) -> str:
        """  """
        try:
            audio_output_path = self.extract_audio_from_video(filename)
            logger.info(f'视频要先转为音频文件: {audio_output_path}')
            response = self.audio_recognizer.get_response(audio_output_path)
            return response
        except Exception as e:
            return f"读取视频件时发生错误. {filename}, Error: {e}"
