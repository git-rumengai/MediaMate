import asyncio
from mediamate.config import config     # 必须在导入metagpt工具包之前添加这一行以确保环境变量正确

from metagpt.roles import Searcher


async def main():
    await Searcher().run("最近3天关于AI的新闻")


if __name__ == "__main__":
    asyncio.run(main())
