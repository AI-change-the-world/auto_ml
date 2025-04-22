from openai import OpenAI

from db.tool_model.tool_model import ToolModel


def get_model(tool_model: ToolModel) -> OpenAI:
    return OpenAI(api_key=tool_model.api_key, base_url=tool_model.base_url)
