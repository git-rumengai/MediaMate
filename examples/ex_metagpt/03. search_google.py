import asyncio
from mediamate.config import config     # 必须在导入metagpt工具包之前添加这一行以确保环境变量正确

from metagpt.roles import Searcher


async def main():
    # Role:
    # 1. 初始化: set_actions, 只有一个 SearchAndSummarize
    # 1. _observe, 保存, 过滤消息放到"self.rc.news"中
    # 2. react -> _react -> _think: 判断下一步动作(self.rc.todo: SearchAndSummarize)
    # 3. _act: 执行自定义的动作(执行self.rc.todo.run: SearchAndSummarize.run)
    # 4. publish_message: 输出消息
    await Searcher().run("最近3天关于AI的新闻")


if __name__ == "__main__":
    asyncio.run(main())
