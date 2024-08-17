import asyncio
from mediamate.config import config     # 必须在导入metagpt工具包之前添加这一行以确保环境变量正确

from metagpt.roles.researcher import RESEARCH_PATH, Researcher


async def main():
    # 1. set_actions: [CollectLinks, WebBrowseAndSummarize, ConductResearch]和_set_react_mode: BY_ORDER
    # 2. CollectLinks:
    #   - 根据主题提取2个关键词
    #   - 根据两个关键词搜素出16个结果
    #   - 根据16个结果提取4个相关子主题
    #   - 每个子主题搜索8个结果并保留其中4个和主题最相关的结果
    #   - 将 主题 和 urls 整理成 Report 类型并继续
    # 3. WebBrowseAndSummarize:
    #   - 逐个浏览url并进行总结
    #   - 将 主题 和 summaries 整理成Report类型并继续
    # 4. ConductResearch:
    #   - 用一个提示词将所有内容整理成报告输出
    #   - 将结果整理成Report继续
    # 5. 使用 write_report 方法将结果保存到本地
    
    topic = "小红书新号快速涨粉操作手册"
    role = Researcher(language="zh-cn")
    await role.run(topic)
    print(f"save report to {RESEARCH_PATH / f'{topic}.md'}.")


if __name__ == "__main__":
    asyncio.run(main())
