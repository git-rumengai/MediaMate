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
        print(lines)
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
        # news = ['媒体: 36氪, 更新时间: 10 分钟前\n\n\n1. 8点1氪｜宗馥莉接手娃哈哈集团公司股份；中金公司降职降薪传言属实；部分地方恢复或新建国道收费站\n\n\n详情: 宗馥莉接手娃哈哈集团股份；中金公司降职降薪传言属实；部分地方恢复或新建国道收费站。\n\n\n2. 高端市场再战苹果，华为Mate 70最缺的是生态？\n\n\n3. 今年最香活法，收割了多少抠门中产\n\n\n4. 抢先华为一步，「非洲手机之王」发布三折叠原型机\n\n\n5. 在印度卖五金配件，这家公司年销破3亿｜出海New Land\n\n\n6. OpenAI大逃亡，AGI安全团队半数出走，奥特曼：攘外必先安内\n\n\n7. 中国大学跌得最惨的专业，从“天选”变“天坑”\n\n\n8. 智能投影仪卖不动了，画质短板是罪魁祸首？', '媒体: 少数派, 更新时间: 9 分钟前\n\n\n1. 社区速递 059 | 你没见过的社区文章、一周最热评、派友的黑神话体验\n\n\n详情: 社区速递059介绍了众多社区文章，包括一周热评和派友的黑神话体验。内容涵盖自荐的作者投稿、播客讨论、科技产品评测，以及黑神话游戏的玩家反馈与体验，展现了多样化的社区文化。\n\n\n2. 派评 | 近期值得关注的 App\n\n\n3. 本周看什么 | 最近值得一看的 7 部作品\n\n\n4. 把女朋友拍好看，技巧可能没有你以为的那么重要\n\n\n5. 键盘鼠标都最低，派商店 Keychron 系列清仓促销专场\n\n\n6. 社区速递 058 | 你没见过的社区文章、一周最热评、派友在用的电纸书\n\n\n7. 派评 | 近期值得关注的 App\n\n\n8. 不买可以先收藏 15：如何做一锅好吃的米饭\n\n\n9. 《黑神话：悟空》评测：敢问路在何方，路在脚下\n\n\n10. 本周看什么 | 最近值得一看的 7 部作品\n\n\n11. 新玩意 191｜少数派的编辑们最近买了啥？\n\n\n12. 一台更实用的「iPhone」：小米 14 半年体验\n\n\n13. 派评 | 近期值得关注的 App\n\n\n14. Mac 版虽迟但到：老牌阅读器 Unread 推出 4.0 大更新\n\n\n15. 心中无工作天天放假，手边有鱼摸劳逸结合\n\n\n16. 有争议，无悬念：我的一年期 MacBook Pro使用记录与随想\n\n\n17. 派评 | 近期值得关注的 App\n\n\n18. 本周看什么 | 最近值得一看的 8 部作品\n\n\n19. 七夕送礼不抓狂，这是派商店为你准备的送礼清单\n\n\n20. 2024 年，我是如何使用 Windows PC 的', '媒体: 虎嗅网, 更新时间: 10 分钟前\n\n\n1. 小米逆天改命\n\n\n详情: 小米在2024年推出电动车，Q2交付2.73万辆，收入62亿，尽管亏损，但其智能汽车有望改变公司估值逻辑，未来前景乐观。雷军的领导下，小米电动车研发投入显著，或实现盈利潜力。\n\n\n2. 没想到房子老龄化的程度会这么严重\n\n\n3. 租金回到十年前，餐饮人却不敢开新店了\n\n\n4. 县城的产业，越来越硬核了\n\n\n5. 资本一夜抽逃英伟达\n\n\n6. 3分钟千人被裁，IBM中国大败退\n\n\n7. 谁把四大行买出了新高？\n\n\n8. 餐饮“天花板”，塌了？\n\n\n9. 半年倒闭近3万家，高端面馆正“狼狈退场”\n\n\n10. 县城的低配山姆：没有中产，只有中年\n\n\n11. 字节的野心藏不住了\n\n\n12. 中国大学跌得最惨的专业，从“天选”变“天坑”\n\n\n13. 鼎泰丰扛不住了\n\n\n14. BBA车主的面子，被“假货三件套”背刺\n\n\n15. 261亿港元，维达被卖了', '媒体: 果壳, 更新时间: 10 分钟前\n\n\n1. 为了攻克致命传染病，我想先“治愈”蚊子\n\n\n2. 自行消失的红斑、游走的关节疼痛，我在果壳病人翻到了同款儿童病例\n\n\n3. 一股牙膏味的薄荷巧克力，是甜品界自己的“折耳根”\n\n\n4. 全红婵在空中转圈的时候，睁眼了吗？\n\n\n5. 网友操心的乒乓球抠裤子这个事儿，我们终于分析完毕了\n\n\n6. 糖水里放鹌鹑蛋就害怕了？还可以加腐竹和海带呢！\n\n\n7. 中国乒乓，不断前行\n\n\n8. 郑钦文，红土球场上最坚韧的那个人\n\n\n9. 被问了100遍的学科短视频来啦！10个神仙博主，让娃爱上学习！\n\n\n10. 探索世界的第一步：给宝宝一个自信的开始', '媒体: IT之家, 更新时间: 9 分钟前\n\n\n1. 高通骁龙 6 Gen 3 处理器发布：三星 4nm 工艺、2.4GHz CPU\n\n\n详情: 高通骁龙 6 Gen 3 处理器于2024年9月1日发布，采用三星4nm工艺，CPU主频为2.4GHz，具有4×2.40GHz Cortex A78和4×1.80GHz Cortex A55。与前代相比，CPU性能提升10%，GPU性能提升30%，AI性能提升20%。\n\n\n2. 小米米家多功能电煮锅 1.5L 上架：1000W 功率、5 挡火力可调，售 149 元\n\n\n3. 鸿蒙智行 8 月全系交付新车 33699 辆、环比下降约 23.6%，1-8 月累计交付超 27 万辆\n\n\n4. 北汽极狐 8 月销量首次破万达 10001 辆，1-8 月销量 35861 辆同比增长 198%\n\n\n5. 古尔曼：M4 Pro 芯片版 Mac mini 将不会提供 USB-A 端口\n\n\n6. 华为见非凡品牌盛典及鸿蒙智行新品发布会定档 9 月 10 日，余承东预告“最具颠覆性产品”\n\n\n7. 余承东官宣问界 M9 五座版：9 月 10 日发布，大五座旗舰 SUV\n\n\n8. 比亚迪 8 月汽车销量 373083 辆，同比增长 36%\n\n\n9. 比亚迪各车型 8 月详细销量信息公布：秦家族超 7 万辆，海鸥超 4 万辆\n\n\n10. 长安 Lumin 清悦款微型车上市：售 3.79 万元，可享 2 万元国家以旧换新补贴\n\n\n11. 国产 GPU 企业象帝先回应解散传闻：公司未解散或清算，正进行人员优化\n\n\n12. 一汽丰田 8 月销量 72086 台，全新亚洲龙销售 9264 台']
        containers = []
        for content in news:
            title_text, content = content.split(self.sep, maxsplit=1)
            print('66'*66)
            print(title_text)
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

            # 4. 下方按照顺序出现新闻, 左对齐
            adj_index = 0
            font_size = 20
            est_text = '这是一段测试字体宽度的代码'
            previous_news = MarkupText(est_text, font_size=font_size)
            total_text_width = previous_news.width
            char_width = 0 # total_text_width / len(est_text)
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
