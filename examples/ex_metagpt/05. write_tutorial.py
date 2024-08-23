import asyncio
from mediamate.config import config     # 必须在导入metagpt工具包之前添加这一行以确保环境变量正确

from metagpt.roles.tutorial_assistant import TutorialAssistant


async def main():
    # 1. set_actions: WriteDirectory, _set_react_mode: BY_ORDER
    # 2. 创建教程目录
    # 3. 遍历教程目录, 每个子目录都创建一个 WriteContent对象
    # 4. 重新设置set_actions和max_react_loop
    # 5. 等待子目录创建的action全部执行完毕
    # 6.
    topic = '撩妹教程'
    role = TutorialAssistant(language="Chinese")
    await role.run(topic)


if __name__ == "__main__":
    asyncio.run(main())
