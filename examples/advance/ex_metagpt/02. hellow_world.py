import asyncio
from metagpt.llm import LLM
from metagpt.logs import logger


async def ask_and_print(question: str, llm: LLM, system_prompt) -> str:
    logger.info(f"Q: {question}")
    rsp = await llm.aask(question, system_msgs=[system_prompt])
    logger.info(f"A: {rsp}")
    return rsp


async def lowlevel_api_example(llm: LLM):
    logger.info("low level api example")
    # 批量提问, 结果通过'\n'连接的字符串
    logger.info(await llm.aask_batch(["hi", "write python hello world."]))

    hello_msg = [{"role": "user", "content": "count from 1 to 10. split by newline."}]
    # 返回对象
    logger.info(await llm.acompletion(hello_msg))
    # 返回 ChatCompletion 对象
    logger.info(await llm.acompletion_text(hello_msg))
    # 返回字符串结果
    # streaming mode, much slower
    await llm.acompletion_text(hello_msg, stream=True)

    # check completion if exist to test llm complete functions
    if hasattr(llm, "completion"):
        logger.info(llm.completion(hello_msg))


async def main():
    llm = LLM()
    await ask_and_print("what's your name?", llm, "I'm a helpful AI assistant.")
    await ask_and_print("who are you?", llm, "just answer 'I am a robot' if the question is 'who are you'")
    await lowlevel_api_example(llm)


if __name__ == "__main__":
    asyncio.run(main())
