import json
from pydantic import BaseModel, ValidationError
from typing import Type, Tuple, Any

from mediamate.tools.api_market.base import BaseMarket
from mediamate.utils.log_manager import log_manager
from mediamate.tools.api_market.chat import Chat


logger = log_manager.get_logger(__name__)


class LLMPydantic:
    """  """
    def __init__(self):
        self.chat = Chat()

    def get_llm_response(self, llm: BaseMarket, prompt: str, response_type: Type[BaseModel]) -> BaseModel:
        """
        从 LLM 的 response 中提取并校验特定类型的数据。

        :param prompt: LLM 的 prompt
        :param response_type: Pydantic 模型类，用于校验解析后的数据
        :return: 校验结果，成功返回 (True, 解析后的数据)，失败返回 (False, 错误信息)
        """
        model_name = response_type.__name__
        model_schema = response_type.schema_json(ensure_ascii=False)
        full_prompt = prompt.replace(model_name, model_schema)
        logger.info(full_prompt)
        ai_response = llm.get_response(full_prompt)
        flag, parsed_data = self.parse_response(ai_response, response_type)
        if flag:
            return parsed_data
        logger.error(
            f'LLM 解析结果出错: 无法解析为 {response_type.__name__}. 原始响应: {ai_response[:100]}...')  # 截取前100字符的原始响应进行日志记录
        return response_type()  # 返回空的 Pydantic 模型实例

    def get_response_model(self, ai_response: str, response_type: Type[BaseModel]) -> BaseModel:
        """
        从 LLM 的 response 中提取并校验特定类型的数据。

        :param prompt: LLM 的 prompt
        :param response_type: Pydantic 模型类，用于校验解析后的数据
        :return: 校验结果，成功返回 (True, 解析后的数据)，失败返回 (False, 错误信息)
        """
        flag, parsed_data = self.parse_response(ai_response, response_type)
        if flag:
            return parsed_data
        logger.error(
            f'LLM 解析结果出错: 无法解析为 {response_type.__name__}. 原始响应: {ai_response[:100]}...')  # 截取前100字符的原始响应进行日志记录
        return response_type()  # 返回空的 Pydantic 模型实例

    def extract_json(self, text: str) -> str:
        """
        从文本中提取 JSON 数据，支持任意类型的嵌套 JSON 对象和数组。
        """
        start = -1
        brace_count = 0
        bracket_count = 0
        in_quotes = False
        for i, char in enumerate(text):
            if char == '"' and (i == 0 or text[i - 1] != '\\'):  # 检查是否在引号内
                in_quotes = not in_quotes
            elif char == '{' and not in_quotes:  # 开始新的 JSON 对象
                if start == -1:
                    start = i
                brace_count += 1
            elif char == '}' and not in_quotes:  # 结束一个 JSON 对象
                brace_count -= 1
                if brace_count == 0 and bracket_count == 0 and start != -1:
                    json_str = text[start:i + 1]
                    # 替换换行符为 \n
                    json_str = json_str.replace('\n', '\\n')
                    return json_str
            elif char == '[' and not in_quotes:  # 开始新的数组
                if start == -1:
                    start = i
                bracket_count += 1
            elif char == ']' and not in_quotes:  # 结束一个数组
                bracket_count -= 1
                if brace_count == 0 and bracket_count == 0 and start != -1:
                    json_str = text[start:i + 1]
                    # 替换换行符为 \n
                    json_str = json_str.replace('\n', '\\n')
                    return json_str
        return ""

    def parse_response(self, ai_response: str, model: Type[BaseModel]) -> Tuple[bool, Any]:
        """
        解析并校验 AI 回复中的 Pydantic 模型数据。

        :param ai_response: AI 的回复内容，可能包含 JSON 数据及其他文本
        :param model: Pydantic 模型类，用于校验解析后的数据
        :return: 校验结果，成功返回 (True, 解析后的数据)，失败返回 (False, 错误信息)
        """
        try:
            # 提取 JSON 数据
            json_str = self.extract_json(ai_response)
            if not json_str:
                return False, '未找到有效的 JSON 数据'
            parsed_data = json.loads(json_str)
            validated_data = model.parse_obj(parsed_data)
            return True, validated_data
        except json.JSONDecodeError as e:
            logger.info(f'JSON 解析错误: {e}')
            return False, f'JSON 解析错误: {e}'
        except ValidationError as e:
            logger.info(f'数据校验错误: {e}')
            return False, f'数据校验错误: {e}'


llm_pydantic = LLMPydantic()


__all__ = ['LLMPydantic']


if __name__ == '__main__':
    js_str = """```json\n{\n  \"title\": \"书店里的下午茶时光\",\n  \"description\": \"在朵云书院，享受一杯温暖的拿铁与精致的小点心，翻阅新书，沉浸在宁静的下午茶时光中。让阅读与美味相伴。\",\n  \"keywords\": [\"下午茶\", \"朵云书院\", \"阅读\"]\n}\n```"""
    result = llm_pydantic.extract_json(js_str)
    print(result)
