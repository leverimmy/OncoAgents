import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()

def get_client(name: str) -> OpenAIChatCompletionClient:
    if name in ["gpt-4o", "o3", "gpt-5-mini"]:
        return OpenAIChatCompletionClient(
            model=name,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
        )
    else:
        return OpenAIChatCompletionClient(
            model=name,
            model_info={
                "temperature": 0.7,
                "max_tokens": 8192,
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "family": "siliconflow",
                "structured_output": True
            },
            api_key=os.getenv("SILICON_FLOW_API_KEY"),
            base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
        )
