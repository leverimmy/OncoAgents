import asyncio
import json
from autogen_agentchat.messages import UserMessage
from src.backend import model_client
from src.json_schema import RATIONAL_JSON_SCHEMAS, EMOTIONAL_JSON_SCHEMA, REPLY_JSON_SCHEMA
from src.prompt import RATIONAL_PROMPTS, EMOTIONAL_PROMPTS, REPLY_PROMPTS
from typing import Dict
from src.utils import logger, SafeDict, STAGE_PI, STAGE_S

class EmotionalPatient:
    def __init__(self, user_profile: str) -> None:
        self.user_profile = user_profile
        self.client = model_client
        self.emotion_stage = STAGE_PI

        self.state = {
            "emotion_state": "",
            "knowledge": "",
            "information_gap": "",
            "ers_score": 0,
            "trs_score": 0,
            "ccs_score": 0,
            "tas_score": 0,
        }
    
    def update_state(self, reply: Dict[str, str]) -> None:
        for key in self.state.keys():
            if key in reply:
                self.state[key] = reply[key]

    async def run_rational_cot(self, dialogue_history: Dict[str, str], is_transfer: bool = False) -> Dict[str, str]:
        # TODO: transfer 的状态转移的情况还没有处理
        format_args = SafeDict(
            user_profile = self.user_profile,
            dialogue_history = dialogue_history,
            knowledge = self.state["knowledge"],
            information_gap = self.state["information_gap"]
        )

        rational_cot = await self.client.create(
            messages=[UserMessage(
                content=RATIONAL_PROMPTS[self.emotion_stage].format_map(format_args),
                source="User"
            )],
            json_output=RATIONAL_JSON_SCHEMAS[self.emotion_stage],
        )

        json_result = json.loads(rational_cot.content)
        logger.info(f"Rational CoT Result: {json_result}")
        return json_result

    async def run_emotional_cot(self, dialogue_history: Dict[str, str]) -> Dict[str, str]:
        format_args = SafeDict(
            user_profile = self.user_profile,
            dialogue_history = dialogue_history,
            emotion_state = self.state["emotion_state"],
            ers_score = self.state["ers_score"],
            trs_score = self.state["trs_score"]
        )
    
        emotional_cot = await self.client.create(
            messages=[UserMessage(
                content=EMOTIONAL_PROMPTS[self.emotion_stage].format_map(format_args),
                source="User"
            )],
            json_output=EMOTIONAL_JSON_SCHEMA,
        )
        logger.info(f"Emotional CoT Result: {emotional_cot.content}")
        return json.loads(emotional_cot.content)
    
    async def run_reply(self, dialogue_history: Dict[str, str], current_state: Dict[str, str]) -> Dict[str, str]:
        format_args = SafeDict(
            user_profile = self.user_profile,
            dialogue_history = dialogue_history,
            input_analysis = current_state.get("input_analysis", ""),
            stage_analysis = current_state.get("stage_analysis", ""),
            emotion_analysis = current_state.get("emotion_analysis", ""),
            emotion_state = current_state.get("emotion_state", ""),
            ers_score = current_state.get("ers_score", ""),
            trs_analysis = current_state.get("trs_analysis", ""),
            trs_score = current_state.get("trs_score", ""),
            knowledge = current_state.get("knowledge", ""),
            information_gap = current_state.get("information_gap", ""),
            ccs_score = current_state.get("ccs_score", ""),
            tas_score = self.state["tas_score"],
        )

        reply = await self.client.create(
            messages=[UserMessage(
                content=REPLY_PROMPTS[self.emotion_stage].format_map(format_args),
                source="User"
            )],
            json_output=REPLY_JSON_SCHEMA,
        )
        logger.info(f"Reply Result: {reply.content}")
        return json.loads(reply.content)

    async def respond(self, dialogue_history: Dict[str, str]) -> Dict[str, int | str] | None:
        # 并行运行 rational_cot 和 emotional_cot
        rational_cot, emotional_cot = await asyncio.gather(
            self.run_rational_cot(dialogue_history),
            self.run_emotional_cot(dialogue_history),
        )
        current_state = dict(emotional_cot)

        if rational_cot.get("stage_transfer", False):
            logger.info("Stage transfer occurred!")
            self.emotion_stage = min(self.emotion_stage + 1, STAGE_S)
            new_rational_cot = await self.run_rational_cot(dialogue_history, is_transfer=True)
            current_state.update(new_rational_cot)
        else:
            current_state.update(rational_cot)

        # 运行 run_reply 生成回复
        try:
            reply = await self.run_reply(dialogue_history, current_state)
            current_state.update(reply)
            current_state['stage'] = self.emotion_stage
            self.update_state(current_state)
            return current_state
        except Exception as e:
            logger.error(f"Error in EmotionalPatient respond: {e}")
            return None
    