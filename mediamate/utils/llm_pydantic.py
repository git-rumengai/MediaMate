from pydantic import BaseModel, ValidationError
from typing import Type, Tuple, Any
import json


def extract_json(text: str) -> str:
    """
    从文本中提取 JSON 数据，支持任意类型的嵌套 JSON 对象和数组。

    :param text: 包含 JSON 数据的文本
    :return: 提取出的 JSON 字符串，如果找不到则返回空字符串
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
                return text[start:i + 1]
        elif char == '[' and not in_quotes:  # 开始新的数组
            if start == -1:
                start = i
            bracket_count += 1
        elif char == ']' and not in_quotes:  # 结束一个数组
            bracket_count -= 1
            if brace_count == 0 and bracket_count == 0 and start != -1:
                return text[start:i + 1]

    return ""


def parse_response(ai_response: str, model: Type[BaseModel]) -> Tuple[bool, Any]:
    """
    解析并校验 AI 回复中的 Pydantic 模型数据。

    :param ai_response: AI 的回复内容，可能包含 JSON 数据及其他文本
    :param model: Pydantic 模型类，用于校验解析后的数据
    :return: 校验结果，成功返回 (True, 解析后的数据)，失败返回 (False, 错误信息)
    """
    try:
        # 提取 JSON 数据
        json_str = extract_json(ai_response)
        if not json_str:
            return False, "未找到有效的 JSON 数据"
        # 解析 JSON 数据
        parsed_data = json.loads(json_str)
        # 使用 Pydantic 模型校验解析后的数据
        validated_data = model.parse_obj(parsed_data)
        return True, validated_data
    except json.JSONDecodeError as e:
        return False, f"JSON 解析错误: {e}"
    except ValidationError as e:
        return False, f"数据校验错误: {e}"
