import re
import os
import requests
from pydub import AudioSegment
from typing import List

import mediamate.tools.free_media.free_pexels
from mediamate.config import config, ConfigManager
from mediamate.tools.api_market.generator import OpenAIAudioGenerator
from mediamate.tools.api_market.recognizer import OpenAIAudioRecognizer
from mediamate.tools.api_market.chat import Chat
from mediamate.tools.free_media.free_pexels import FreePexels
from mediamate.utils.enums import VideoOrientation


class CreateVideo:
    def __init__(self, data_path: str = ''):
        self.chat = Chat()
        self.free_pexels = FreePexels()
        self.data_path = data_path
        metafilename = os.path.join(data_path, 'metadata.yaml')
        self.metadata = ConfigManager(metafilename)
        self.free_media_config = self.metadata.get('free_media')

    def update_config(self):
        self.metadata.set('free_media', self.free_media_config)

    def get_script(self) -> {}:
        """ 规范化之后的文案内容, 默认第一行是标题 """
        filename = self.free_media_config.get('script')
        fullname = os.path.join(self.data_path, filename)
        with open(fullname, 'r') as f:
            content = f.read()
        title, content = content.split("\n\n", maxsplit=1)
        return {'title': title, 'content': content}

    def update_script(self) -> List[str]:
        """ 将脚本规范化 """
        filename = self.free_media_config.get('script')
        fullname = os.path.join(self.data_path, filename)
        with open(fullname, 'r') as f:
            content = f.read()
        paragraphs = content.split('\n\n')  # 假设段落之间有两个换行符
        paragraphs = [p.strip() for p in paragraphs if p.strip()]  # 去除空白段落
        if len(paragraphs) < 2:
            sentences = re.split(r'(?<=[。！？])', content)  # 按句号、问号和感叹号分割
            paragraphs = []
            paragraph = ''
            for sentence in sentences:
                if len(paragraph) + len(sentence) < 30:  # 假设每个段落至少30个字符
                    paragraph += sentence
                else:
                    paragraphs.append(paragraph.strip())
                    paragraph = sentence
            if paragraph:
                paragraphs.append(paragraph.strip())
        content = '\n\n'.join(paragraphs)
        with open(fullname, 'w') as f:
            f.write(content)
        return paragraphs

    def generate_audio(self):
        """ 文本 -> 语音 """
        script = self.get_script()
        content = script['content']
        oag = OpenAIAudioGenerator()
        response = oag.get_response(content)
        name, _ = os.path.splitext(self.free_media_config['script'])
        # 新的文件名与.wav后缀合并
        filename = f"{name}.wav"
        fullname = os.path.join(self.data_path, filename)
        with open(fullname, 'rb') as f:
            f.write(response)
        self.free_media_config['audio'] = filename
        self.update_config()

    def generate_srt(self):
        """ 语音 -> 字幕(302ai暂时不支持), 再用llm校对字幕 """
        script = self.get_script()
        content = script['content']
        filename = self.free_media_config.get('audio')
        audio_path = os.path.join(self.data_path, filename)
        audio = AudioSegment.from_wav(audio_path)

    def generate_video_materials(self):
        """ 下载视频片段 """
        materials_path = f'{self.data_path}/materials_path'
        os.makedirs(materials_path, exist_ok=True)
        script = self.get_script()
        orientation = self.free_media_config.get('orientation')
        orientation = VideoOrientation.PORTRAIT if orientation == [16, 9] else VideoOrientation.LANDSCAPE
        content = script['content']
        pargraphs = content.split('\n\n')
        for i, paragraph in enumerate(pargraphs):
            urls = self.free_pexels.get_video(paragraph, number=3, orientation=orientation)
            for j, url in enumerate(urls):
                response = requests.get(url)
                with open(f'{materials_path}/{i:04}-{j:04}.mp4', 'wb') as f:
                    f.write(response.content)

    def combine_video(self):
        """ 合并视频 """



# 1. 确定主题
# 2. 生成视频脚本
# 3. 提取生成视频的关键词

# 4. 生成音频

# 5. 生成字幕

# 6. 下载视频材料

# 7. 合成视频



