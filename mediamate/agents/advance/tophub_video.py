from typing import Tuple
import asyncio

from manim import *

from mediamate.utils.enums import TophubType
from mediamate.tools.tophub.ranking import Ranking
from mediamate.tools.duckduckgo.web_summary import WebSummary


class TophubVideo(Scene):
    def __init__(self, channel: str='RuMengAI新闻', tophub_type: TophubType = TophubType.TECH):
        super().__init__()
        self.channel = channel
        self.tophub_type = tophub_type
        self.web_summary = WebSummary()
        self.sep = '\n\n\n'

    def wrap_text(self, text, font_size, max_width, char_width: float = 0., color=WHITE):
        """  """
        if char_width:
            estimated_char_width = char_width
        else:
            temp_text = MarkupText(text, font_size=font_size)
            total_text_width = temp_text.width
            estimated_char_width = total_text_width / len(text)
        max_chars_per_line = int(max_width / estimated_char_width)
        lines = []
        for i in range(0, len(text), max_chars_per_line):
            lines.append(text[i:i + max_chars_per_line])
        text_objects = [MarkupText(line, font_size=font_size, color=color) for line in lines]
        return text_objects

    async def get_format_news(self, news: Dict):
        """  """
        result = f"""媒体: {news['媒体']}, 更新时间: {news['时间']}"""
        for index, n in enumerate(news['内容']):
            result += f'{self.sep}{n["标题"]}'
            if index == 0:
                query, url = n['标题'], n['链接']
                summary = await self.web_summary.summary([{query: url}])
                summary_text = summary[0][query]
                if 'ERROR' not in summary_text:
                    result += f'{self.sep}详情: {summary_text}'
        return result

    async def get_tophub(self) -> Tuple[...]:
        """  """
        news = await Ranking().get_data(tophub=(self.tophub_type,))
        news = news[0].get(self.tophub_type.value, [])
        tasks = [asyncio.ensure_future(self.get_format_news(n)) for n in news[:5]]
        result = await asyncio.gather(*tasks)
        return result

    def construct(self):
        """  """
        # 创建一个带有坐标轴和网格的平面
        channel_pos = [5.0, 3.5, 0]
        line_start_pos = [-6.5, 3.0, 0]
        line_width = 12

        channel_width = config.frame_width * 0.8
        channel = MarkupText(self.channel, color=utils.color.random_color(), width=channel_width)
        self.play(Write(channel), run_time=1)
        channel_scale = config.frame_width * 0.2 / channel_width
        self.play(channel.animate.scale(channel_scale).move_to(np.array(channel_pos)), run_time=1)

        # 3. 字体下方逐渐出现一条横线, 宽度距离屏幕左右两侧1/5的位置
        line_end_pos = [line_start_pos[0] + line_width, line_start_pos[1], line_start_pos[2]]
        start, end = np.array(line_start_pos), np.array(line_end_pos)
        line = Line(start=start, end=end, color=utils.color.random_color())
        self.play(Create(line), run_time=1)

        loop = asyncio.get_event_loop()
        news = loop.run_until_complete(self.get_tophub())
        containers = []
        for content in news:
            title_text, content = content.split(self.sep, maxsplit=1)
            if len(containers) > 0:
                self.wait(3)
                for mb in containers:
                    self.remove(mb)
            title = MarkupText(title_text, color=WHITE, font_size=24)
            # 计算第一个字的位置
            first_char_position = title.get_corner(UL)
            offset = np.array([line_start_pos[0], channel_pos[1], 0]) - first_char_position
            title.shift(offset)

            self.play(FadeIn(title), run_time=0.5)
            containers.append(title)
            content_news = content.split(self.sep)

            adj_index = 0
            font_size = 20
            est_text = '这是一段测试字体宽度的代码'
            previous_news = MarkupText(est_text, font_size=font_size)
            total_text_width = previous_news.width
            char_width = total_text_width / len(est_text)
            for index, inner_content in enumerate(content_news[:8]):
                if index == 0:
                    content_news = self.wrap_text(f'1. {inner_content}', font_size=font_size, max_width=line_width, char_width=char_width)
                    for inner_index, inner_news in enumerate(content_news):
                        if inner_index == 0:
                            inner_news.next_to(line, DOWN).align_to(line, LEFT)
                            previous_news = inner_news
                        else:
                            inner_news.next_to(previous_news, DOWN).align_to(line, LEFT)
                            previous_news = inner_news
                else:
                    if inner_content.startswith('详情: '):
                        adj_index -= 1
                        content_news = self.wrap_text(f'- {inner_content}', font_size=font_size, max_width=line_width, char_width=char_width)
                        for inner_news in content_news:
                            inner_news.next_to(previous_news, DOWN).align_to(line, LEFT)
                            previous_news = inner_news
                    else:
                        content_news = self.wrap_text(f'{index + 1 + adj_index}. {inner_content}', font_size=font_size, max_width=line_width, char_width=char_width)
                        for inner_news in content_news:
                            inner_news.next_to(previous_news, DOWN).align_to(line, LEFT)
                            previous_news = inner_news

                for cn in content_news:
                    self.play(FadeIn(cn), run_time=0.5)
                    containers.append(cn)

        self.wait(5)


import subprocess
from pathlib import Path


if __name__ == "__main__":
    # 构建命令行参数
    script_name = Path(__file__).resolve()

    # 传递文件名和场景类名到manim命令行工具
    command = ["manim", '-pql', str(script_name), 'TophubVideo', '--disable_caching', '']
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    print(result.stderr)

    # with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8') as process:
    #     # 逐行读取标准输出
    #     for line in process.stdout:
    #         logger.info(line)
    #     for line in process.stderr:
    #         logger.error(line)
