import asyncio
import json

from autogen_agentchat.messages import UserMessage

from src.backend import get_client
from src.json_schema import (
    EMOTIONAL_JSON_SCHEMA,
    RATIONAL_JSON_SCHEMAS,
    REPLY_JSON_SCHEMA,
)
from src.prompt import EMOTIONAL_PROMPTS, RATIONAL_PROMPTS, REPLY_PROMPTS
from src.utils import NAME2STAGE, STAGE_PI, SafeDict, logger


class EmotionalPatient:
    def __init__(self, user_profile: str, model_name: str) -> None:
        self.user_profile = user_profile
        self.model_name = model_name
        self.client = get_client(model_name)
        self.emotion_stage = STAGE_PI

        self.state = {
            "emotion_state": "",
            "knowledge": "",
            "information_gap": "",
            "ccs_score": 0,
            "ess_score": 0,
            "pas_score": 0,
        }

    def update_state(self, current_state: dict[str, str]) -> None:
        for key in self.state.keys():
            if key in current_state:
                self.state[key] = current_state[key]

    # TODO: dialogue_history 的类型感觉不一致
    async def run_rational_cot(
        self, dialogue_history: dict[str, str]
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            knowledge=self.state["knowledge"],
            information_gap=self.state["information_gap"],
            ccs_score=self.state["ccs_score"],
        )

        rational_cot = await self.client.create(
            messages=[
                UserMessage(
                    content=RATIONAL_PROMPTS[self.emotion_stage].format_map(
                        format_args
                    ),
                    source="User",
                )
            ],
            json_output=RATIONAL_JSON_SCHEMAS[self.emotion_stage],
        )

        json_result = json.loads(rational_cot.content)
        logger.info(f"Rational CoT Result: {json_result}")
        return json_result

    async def run_emotional_cot(
        self, dialogue_history: dict[str, str]
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            emotion_state=self.state["emotion_state"],
            ess_score=self.state["ess_score"],
        )

        emotional_cot = await self.client.create(
            messages=[
                UserMessage(
                    content=EMOTIONAL_PROMPTS[self.emotion_stage].format_map(
                        format_args
                    ),
                    source="User",
                )
            ],
            json_output=EMOTIONAL_JSON_SCHEMA,
        )

        json_result = json.loads(emotional_cot.content)
        logger.info(f"Emotional CoT Result: {json_result}")
        return json_result

    async def run_reply(
        self, dialogue_history: dict[str, str], current_state: dict[str, str]
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            input_analysis=current_state.get("input_analysis", ""),
            knowledge=current_state.get("knowledge", ""),
            information_gap=current_state.get("information_gap", ""),
            ccs_score=current_state.get("ccs_score", ""),
            emotion_state=current_state.get("emotion_state", ""),
            ess_score=current_state.get("ess_score", ""),
            pas_score=self.state["pas_score"],
        )

        reply = await self.client.create(
            messages=[
                UserMessage(
                    content=REPLY_PROMPTS[self.emotion_stage].format_map(format_args),
                    source="User",
                )
            ],
            json_output=REPLY_JSON_SCHEMA,
        )
        logger.info(f"Reply Result: {reply.content}")
        return json.loads(reply.content)

    async def respond(
        self, dialogue_history: dict[str, str]
    ) -> dict[str, int | str] | None:
        # 并行运行 rational_cot 和 emotional_cot
        rational_cot, emotional_cot = await asyncio.gather(
            self.run_rational_cot(dialogue_history),
            self.run_emotional_cot(dialogue_history),
        )
        current_state = {**rational_cot, **emotional_cot}

        # 运行 run_reply 生成回复
        try:
            reply = await self.run_reply(dialogue_history, current_state)

            if NAME2STAGE[reply["stage_transfer"]] != self.emotion_stage:
                logger.info("Stage transfer occurred!")
                self.emotion_stage = NAME2STAGE[reply["stage_transfer"]]

            current_state.update(reply)
            self.update_state(current_state)
            return current_state
        except Exception as e:
            logger.error(f"Error in EmotionalPatient respond: {e}")
            return None
