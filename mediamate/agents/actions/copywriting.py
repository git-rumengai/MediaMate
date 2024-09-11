import re
from typing import List

from pydantic import constr, Field, create_model
from metagpt.actions import Action
from mediamate.utils.log_manager import log_manager

logger = log_manager.get_logger(__name__)


def create_response_model(min_length_content: int = 500):
    # 使用 create_model 动态创建模型
    DynamicResponseModel = create_model(
        'DynamicResponseModel',  # 动态模型的名称
        title=(constr(strip_whitespace=True, min_length=3, max_length=50), Field(..., description="勾子文案风格的标题")),
        content=(constr(strip_whitespace=True, min_length=min_length_content, max_length=min_length_content + 500), Field(..., description="撰写病毒式YouTube视频文案，禁止使用任何语法格式，仅通过换行符划分段落。"))
    )
    return DynamicResponseModel


RESEARCH_BASE_SYSTEM = """你是一个AI写作助手。你的任务是根据给定的主题撰写YouTube视频文案。"""

COPYWRITING_PROMPT = """###
### 参考信息
{content}

### 按照如下schema描述输出标准的JSON格式. 请确保JSON数据没有多余的空格和换行, 只包含最小的必要格式：
{ResponseModel}
"""


class Copywriting(Action):
    """  """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(
        self,
        topic: str,
        content: str,
        min_length_content: int = 500,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> str:
        """  """
        ResponseModel = create_response_model(min_length_content=min_length_content)
        prompt = COPYWRITING_PROMPT.format(content=content, ResponseModel=ResponseModel.schema_json(ensure_ascii=False))
        logger.info(prompt)
        self.llm.auto_max_tokens = True
        return await self._aask(prompt, [system_text])


class ExtractTerm(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


