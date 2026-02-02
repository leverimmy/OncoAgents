import json

from autogen_agentchat.messages import UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel


async def get_llm_output(prompt: str, args: dict, json_schema: BaseModel,
                         client: OpenAIChatCompletionClient) -> dict:
    response = await client.create(
        messages=[
            UserMessage(
                content=prompt.format(**args),
                source="User",
            )
        ],
        json_output=json_schema,
    )
    return json.loads(response.content)
