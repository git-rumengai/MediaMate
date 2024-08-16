import asyncio
from mediamate.config import config     # 必须在导入metagpt工具包之前添加这一行以确保环境变量正确
from metagpt.llm import LLM
from metagpt.logs import logger


async def ask_and_print(question: str, llm: LLM, system_prompt) -> str:
    logger.info(f"Q: {question}")
    rsp = await llm.aask(question, system_msgs=[system_prompt])
    logger.info(f"A: {rsp}")
    logger.info("\n")
    return rsp


async def main():
    # 通过上下文对象创建llm
    llm = LLM()
    # 给出系统提示词并提问
    await ask_and_print("ping?", llm, "Just answer pong when ping.")


if __name__ == "__main__":
    asyncio.run(main())
