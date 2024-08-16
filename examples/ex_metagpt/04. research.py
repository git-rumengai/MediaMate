import asyncio
from mediamate.config import config     # 必须在导入metagpt工具包之前添加这一行以确保环境变量正确

from metagpt.roles.researcher import RESEARCH_PATH, Researcher


async def main():
    topic = "dataiku vs. datarobot"
    role = Researcher(language="en-us")
    await role.run(topic)
    print(f"save report to {RESEARCH_PATH / f'{topic}.md'}.")


if __name__ == "__main__":
    asyncio.run(main())
