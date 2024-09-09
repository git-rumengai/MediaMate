import asyncio

from mediamate.agents.roles.scriptwriter import Scriptwriter
from mediamate.config import config


async def main():
    # 1. set_actions: [CollectLinks, WebBrowseAndSummarize, ConductResearch]和_set_react_mode: BY_ORDER
    # 2. CollectLinks: 输入主题, 输出{'子主题1': ['url1', 'url2', ...], '子主题2': ['url1', 'url2', ...]}
    #   - 根据主题提取2个关键词
    #   - 根据两个关键词搜素出16个结果
    #   - 根据16个结果提取4个相关子主题
    #   - 每个子主题搜索8个结果并保留其中4个和主题最相关的结果
    #   - 将 主题 和 urls 整理成 Report 类型并继续
    # 3. WebBrowseAndSummarize: 输入url列表和子主题, 输出{url1: summary1, url2: summary2, ...}
    #   - 逐个浏览url并进行总结
    #   - 将 主题 和 summaries 整理成Report类型并继续
    # 4. ConductResearch: 输入整篇内容, 输出研究报告
    #   - 用一个提示词将所有内容整理成报告输出
    #   - 将结果整理成Report继续
    # 5. 使用 write_report 方法将结果保存到本地

    topic = """ “一坨尬聊”之后，董宇辉遭遇史上最大危机"""
    role = Scriptwriter()
    role.save_path = f'{config.DATA_DIR}/upload/douyin/RuMengAI/copywriting'
    await role.run(topic)
    print(f"save report to {role.save_path}, topic: {topic}")


if __name__ == "__main__":
    asyncio.run(main())
