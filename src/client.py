import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()

OPENAI_FLAG = True

if OPENAI_FLAG:
    model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL_NAME"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
    )
    vision_model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_VISION_MODEL_NAME"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
    )
else:
    model_client = OpenAIChatCompletionClient(
        model=os.getenv("SILICON_FLOW_MODEL_NAME"),
        model_info={"temperature": 0.7, "max_tokens": 4096, "vision": False, "function_calling": True, "json_output": True, "family": "siliconflow"},
        api_key=os.getenv("SILICON_FLOW_API_KEY"),
        base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
    )
    vision_model_client = OpenAIChatCompletionClient(
        model=os.getenv("SILICON_FLOW_VISION_MODEL_NAME"),
        model_info={"temperature": 0.7, "max_tokens": 4096, "vision": True, "function_calling": True, "json_output": True, "family": "siliconflow"},
        api_key=os.getenv("SILICON_FLOW_API_KEY"),
        base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
    )
