import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()

OPENAI_FLAG = False

# model_client = OpenAIChatCompletionClient(
#     model=os.getenv("OPENAI_MODEL_NAME"),
#     api_key=os.getenv("OPENAI_API_KEY"),
#     base_url=os.getenv("OPENAI_API_BASE_URL"),
# )
vision_model_client = OpenAIChatCompletionClient(
    model=os.getenv("OPENAI_VISION_MODEL_NAME"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)

model_client = OpenAIChatCompletionClient(
    model=os.getenv("SILICON_FLOW_MODEL_NAME"),
    model_info={"temperature": 0.7, "max_tokens": 8192, "vision": False, "function_calling": True, "json_output": True, "family": "siliconflow", "structured_output": True},
    api_key=os.getenv("SILICON_FLOW_API_KEY"),
    base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
)
# vision_model_client = OpenAIChatCompletionClient(
#     model=os.getenv("SILICON_FLOW_VISION_MODEL_NAME"),
#     model_info={"temperature": 0.7, "max_tokens": 8192, "vision": True, "function_calling": True, "json_output": True, "family": "siliconflow", "structured_output": True},
#     api_key=os.getenv("SILICON_FLOW_API_KEY"),
#     base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
# )
if OPENAI_FLAG:
    strategy_model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL_NAME"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
    )
else:
    strategy_model_client = OpenAIChatCompletionClient(
        model=os.getenv("STRATEGY_SILICON_FLOW_MODEL_NAME"),
        model_info={"temperature": 0.7, "max_tokens": 8192, "vision": False, "function_calling": True, "json_output": True, "family": "siliconflow", "structured_output": True},
        api_key=os.getenv("SILICON_FLOW_API_KEY"),
        base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
    )

if False:
    expert_model_client = OpenAIChatCompletionClient(
        model=os.getenv("EXPERT_OPENAI_MODEL_NAME"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
    )
else:
    expert_model_client = OpenAIChatCompletionClient(
        model=os.getenv("EXPERT_SILICON_FLOW_MODEL_NAME"),
        model_info={"temperature": 0.7, "max_tokens": 8192, "vision": False, "function_calling": True, "json_output": True, "family": "siliconflow", "structured_output": True},
        api_key=os.getenv("SILICON_FLOW_API_KEY"),
        base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
    )
if False:
    reply_model_client = OpenAIChatCompletionClient(
        model=os.getenv("REPLY_OPENAI_MODEL_NAME"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
    )
else:
    reply_model_client = OpenAIChatCompletionClient(
        model=os.getenv("REPLY_SILICON_FLOW_MODEL_NAME"),
        model_info={"temperature": 0.7, "max_tokens": 8192, "vision": False, "function_calling": True, "json_output": True, "family": "siliconflow", "structured_output": True},
        api_key=os.getenv("SILICON_FLOW_API_KEY"),
        base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
    )
