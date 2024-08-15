import subprocess
import requests
import os
import base64
from typing import Optional
from mimetypes import guess_type

from mediamate.utils.functions import get_media_type
from mediamate.utils.enums import MediaType
from mediamate.utils.log_manager import log_manager
from mediamate.tools.api_market.recognizer import ImageRecognizer, MediaRecognizer


logger = log_manager.get_logger(__file__)


class ConvertToText:
    """ 将图片/语音/视频转为文本 """
    def __init__(self):
        self.image_recognizer = ImageRecognizer()
        self.media_recognizer = MediaRecognizer()

    def init(self, image_recognizer: Optional[ImageRecognizer] = None, media_recognizer: Optional[MediaRecognizer] = None):
        """  """
        self.image_recognizer = image_recognizer
        self.media_recognizer  = media_recognizer
        return self

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
            response = self.media_recognizer.get_response(filename)
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
            response = self.media_recognizer.get_response(filename)
            return response
        except Exception as e:
            return f"读取视频件时发生错误. {filename}, Error: {e}"


if __name__ == '__main__':
    from mediamate.config import config

    api_key = config.get('302__APIKEY')
    image_recognizer = ImageRecognizer().init(api_key=api_key)
    audio_recognizer = MediaRecognizer().init(api_key=api_key)
    ctt = ConvertToText()
    ctt.init(image_recognizer, audio_recognizer)

    # filename = r'C:\Users\Admin\Desktop\2.png'
    # result = ctt.read_file(filename)
    # print(result)
    #
    # filename = r'C:\Users\Admin\Desktop\雄鹰.wav'
    # result = ctt.read_file(filename)
    # print(result)
    #
    # filename = r'C:\Users\Admin\Desktop\download.mp4'
    # result = ctt.read_file(filename)
    # print(result)

    # url = 'https://ss2.meipian.me/users/2531394/8b3ab230-4016-11eb-a090-d76407546a82.jpg'
    # result = ctt.read_url(url, 'image')
    # print(result)

    # url = 'https://c97f3361a1c971323738e24f451a0225.r2.cloudflarestorage.com/fish-platform-data/task/7c42baa3e702406d8a4f03c0261a6db0.wav?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=45aaffe6f2c5f28b260e2165001da8ad%2F20240814%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240814T060940Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=055a9fab712d502bb32d8dd2a7fcb1b1cdb9161c702262058008e7def7bea0be'
    # result = ctt.read_url(url, 'audio')
    # print(result)
    #
    # url = 'https://v3-web-prime.douyinvod.com/video/tos/cn/tos-cn-ve-15/oQByANHsMF2LVAPQImEDfZfoE1PWgOIFADxbR9/?a=6383&ch=0&cr=0&dr=0&er=0&cd=0%7C0%7C0%7C0&cv=1&br=602&bt=602&cs=0&ds=3&ft=p96FMRLaffPdOW~-N12NvAq-antLjrK-xBl.Rka79QeVvjVhWL6&mime_type=video_mp4&qs=1&rc=OWc1NTM7N2RkPDk2PDNmN0BpMzo0a3k5cjlpdDMzNGkzM0BjNTFeXzItNjAxYl4uNWEuYSNoLzZeMmRzNGxgLS1kLTBzcw%3D%3D&btag=c0000e00028000&cquery=100b&dy_q=1723615895&expire=1723619656&feature_id=46a7bb47b4fd1280f3d3825bf2b29388&l=202408141411351445EA8D4C29130A1401&ply_type=4&policy=4&signature=0b960fb95825c7fa0120e3b4a91d4c92&tk=webid&webid=3c3e9d4a635845249e00419877a3730e2149197a63ddb1d8525033ea2b3354c2fcb74766499cf3c6f79cb8aaebb8ad2f238d9adf46a107ca2cab64707cde3df42bbe0ddf12d441dcd90a0b8277bb88cf9e8e238a05cdb6085c040435f1bde20f7b466e80aa73aecfc457e3d188b457bcf2ea3af492b50f2cebfa4fc6dc1381a91632e2ce795d99aa474d7ce90f615e1189052baa9b1af5df6f12fb2b62740db6-dcc473be9bc3e0183ca718aacb4f0676'
    # result = ctt.read_url(url, 'video')
    # print(result)
