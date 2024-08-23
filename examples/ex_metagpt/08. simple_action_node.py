import asyncio
from mediamate.config import config     # 必须在导入metagpt工具包之前添加这一行以确保环境变量正确

from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger
from metagpt.llm import LLM


LANGUAGE = ActionNode(
    key="语言",
    expected_type=str,
    instruction="提供项目中使用的语言，通常应与用户的需求语言相匹配。",
    example="en_us",
)

PROGRAMMING_LANGUAGE = ActionNode(
    key="编程语言",
    expected_type=str,
    instruction="Python/JavaScript或其他主流编程语言。",
    example="Python",
)

ORIGINAL_REQUIREMENTS = ActionNode(
    key="原始需求",
    expected_type=str,
    instruction="将原始的用户需求放在这里。",
    example="创建2048游戏",
)

PROJECT_NAME = ActionNode(
    key="项目名称",
    expected_type=str,
    instruction="根据“原始需求”的内容，使用蛇形命名风格为项目命名，例如 'game_2048' 或 'simple_crm'。",
    example="game_2048",
)

NODES = [
    LANGUAGE,
    PROGRAMMING_LANGUAGE,
    ORIGINAL_REQUIREMENTS,
    PROJECT_NAME,
]

WRITE_PRD_NODE = ActionNode.from_children("WritePRD", NODES)


async def main():
    prompt = WRITE_PRD_NODE.compile(context="你是一个产品经理，你需要为游戏幻兽帕鲁写需求文档", schema='markdown', mode='auto')
    logger.info(prompt)
    respone = await LLM().aask(prompt)
    logger.info(respone)


if __name__ == '__main__':
    asyncio.run(main())
