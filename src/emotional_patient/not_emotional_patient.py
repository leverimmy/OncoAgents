import json

from autogen_agentchat.messages import UserMessage

from src.backend import get_client
from src.json_schema import NOT_EMOTIONAL_REPLY_JSON_SCHEMA
from src.prompt import NOT_EMOTIONAL_REPLY_PROMPT
from src.utils import SafeDict, logger


class NotEmotionalPatient:
    def __init__(self, user_profile: str, model_name: str) -> None:
        self.user_profile = user_profile
        self.client = get_client(model_name)
        self.state = {
            "tas_score": 0,
        }

    async def run_reply(self, dialogue_history: dict[str, str]) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
        )

        reply = await self.client.create(
            messages=[
                UserMessage(
                    content=NOT_EMOTIONAL_REPLY_PROMPT.format_map(format_args),
                    source="User",
                )
            ],
            json_output=NOT_EMOTIONAL_REPLY_JSON_SCHEMA,
        )
        logger.info(f"Reply Result: {reply.content}")
        return json.loads(reply.content)

    async def respond(self, dialogue_history: dict[str, str]) -> dict[str, str] | None:
        try:
            reply = await self.run_reply(dialogue_history)
            self.state.update(reply)
            return self.state
        except Exception as e:
            logger.error(f"Error in NotEmotionalPatient respond: {e}")
            return None
