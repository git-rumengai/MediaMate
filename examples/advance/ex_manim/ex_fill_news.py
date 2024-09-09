from manim import *


TITLE = '第一财经'
NEWS = [
    '独家 | IBM关闭中国研发部门 涉及员工数量超过1000人, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '居民医保个人缴费增至400元，为何要涨？如何减少缴费"痛感", IBM关闭中国研发部门 涉及员工数量超过1000人',
    '赛诺菲称流感疫苗暂停销售仅为预防措施，但已接种的安全性是否受影响, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '老有所依｜每年上千万人去世，安宁疗护一床难求“如中彩票”, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '深度｜22城试点房屋养老金，资金筹集对业主、财政有何影响, IBM关闭中国研发部门 涉及员工数量超过1000人'
    
    '第二页 独家 | IBM关闭中国研发部门 涉及员工数量超过1000人, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第二页 居民医保个人缴费增至400元，为何要涨？如何减少缴费"痛感", IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第二页 赛诺菲称流感疫苗暂停销售仅为预防措施，但已接种的安全性是否受影响, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第二页 老有所依｜每年上千万人去世，安宁疗护一床难求“如中彩票”, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第二页 深度｜22城试点房屋养老金，资金筹集对业主、财政有何影响, IBM关闭中国研发部门 涉及员工数量超过1000人'
    
    '第三页 独家 | IBM关闭中国研发部门 涉及员工数量超过1000人, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第三页 居民医保个人缴费增至400元，为何要涨？如何减少缴费"痛感", IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第三页 赛诺菲称流感疫苗暂停销售仅为预防措施，但已接种的安全性是否受影响, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第三页 老有所依｜每年上千万人去世，安宁疗护一床难求“如中彩票”, IBM关闭中国研发部门 涉及员工数量超过1000人',
    '第三页 深度｜22城试点房屋养老金，资金筹集对业主、财政有何影响, IBM关闭中国研发部门 涉及员工数量超过1000人'
]


class FillNews(Scene):
    def construct(self):
        """  """
        # title = MarkupText(TITLE, color=utils.color.random_color(), width=config.frame_width - 1)
        # self.play(Write(title), run_time=3)

        title_width = config.frame_width*0.8
        title = MarkupText("第一财经", color=utils.color.random_color(), width=title_width)
        self.play(Write(title), run_time=1)

        # 2. 字体逐渐缩小并停留在屏幕上方正中央
        title_scale = config.frame_width*0.2 / title_width
        self.play(title.animate.scale(title_scale).to_edge(UP), run_time=1)

        # 计算横线的宽度（屏幕帧宽度的 0.8）
        line_width = config.frame_width*0.8
        start_point = LEFT * (line_width / 2)
        end_point = RIGHT * (line_width / 2)

        # 3. 字体下方逐渐出现一条横线, 宽度距离屏幕左右两侧1/5的位置
        line = Line(start=start_point, end=end_point, color=utils.color.random_color()).next_to(title, DOWN)
        self.play(Create(line), run_time=1)

        containers = []
        limit = 5
        # 4. 下方按照顺序出现4条新闻, 左对齐
        for i in range(0, len(NEWS)):
            if i % limit == 0:
                if i != 0:
                    self.wait(3)
                for mb in containers:
                    self.remove(mb)
                previous_news = MarkupText(f'{i+1}. {NEWS[i]}', color=WHITE, width=title_width).next_to(line, DOWN).align_to(line, LEFT)
            else:
                news = MarkupText(f'{i+1}. {NEWS[i]}', color=WHITE, width=title_width).next_to(previous_news, DOWN).align_to(previous_news, LEFT)
                previous_news = news
            # self.play(Write(previous_news), run_time=0.5)
            self.play(FadeIn(previous_news), run_time=0.5)
            # self.play(Create(previous_news), run_time=0.5)
            containers.append(previous_news)

        self.wait(5)


import subprocess
from pathlib import Path

if __name__ == "__main__":
    # 构建命令行参数
    script_name = Path(__file__).resolve()

    # 传递文件名和场景类名到manim命令行工具
    command = ["manim", '-pql', str(script_name), 'FillNews', '--disable_caching']

    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    print(result)
    print(result.stderr)
