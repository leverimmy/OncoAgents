import copy

from src.backend import LanguageModel
from src.prompt.new_new_emotional_patient_prompt import (
    EMOTIONAL_COT_PROMPT,
    EMOTIONAL_REPLY_PROMPT,
    RATIONAL_COT_PROMPT,
    RATIONAL_REPLY_PROMPT,
    REPLY_PROMPTS,
)
from src.utils import SafeDict, logger


class NewNewEmotionalPatient:
    def __init__(self, user_profile: str, model_name: str, url: str | None = None):
        self.user_profile = user_profile
        self.model_name = model_name
        self.model = LanguageModel(model_name=model_name, url=url)

        self.keypoints = {
            "disease_name": [],
            "stage": [],
            "plan": [],
            "course": [],
        }

        self.status = "rational"  # 初始状态设为理性状态

        self.state = {
            "knowledge": [],
            "information_gap": [],
            "trust_analysis": "",
            "emotion_analysis": "",
            "trust_state": "",
            "emotion_state": "",
            "input_analysis": "",
            "ccs_score": 10,
            "ess_score": 0,
            "pas_score": 0,
        }

    def update_state(self, cot: dict[str, str]) -> None:
        for key in self.state.keys():
            if key in cot:
                self.state[key] = cot[key]

    def run_rational_cot(
        self,
        dialogue_history: list[dict[str, str]],
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            knowledge=self.state["knowledge"],
            information_gap=self.state["information_gap"],
            ccs_score=self.state["ccs_score"],
        )
        rational_cot = self.model.chat(
            prompt=RATIONAL_COT_PROMPT.format_map(format_args),
            json_format=True,
        )
        # TODO: 这里可能会出现解析错误，增加异常处理
        logger.info(f"Rational CoT Result: {rational_cot}")
        return rational_cot

    def run_emotional_cot(
        self, dialogue_history: list[dict[str, str]],
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            trust_state=self.state["trust_state"],
            emotion_state=self.state["emotion_state"],
            ess_score=self.state["ess_score"],
        )
        emotional_cot = self.model.chat(
            prompt=EMOTIONAL_COT_PROMPT.format_map(format_args),
            json_format=True,
        )
        # TODO: 这里可能会出现解析错误，增加异常处理
        logger.info(f"Emotional CoT Result: {emotional_cot}")
        return emotional_cot

    def run_reply(
        self,
        dialogue_history: list[dict[str, str]],
        last_status: str,
        current_status: str,
    ) -> dict[str, str]:
        prompt = REPLY_PROMPTS[last_status][current_status]
        if last_status == "rational" and current_status == "rational":
            logger.info("Remaining in rational state.")
        elif last_status == "rational" and current_status == "emotional":
            logger.info("Switching from rational to emotional state.")

        elif last_status == "emotional" and current_status == "emotional":
            logger.info("Remaining in emotional state.")

        elif last_status == "emotional" and current_status == "rational":
            logger.info("Switching from emotional to rational state.")

        reply = {}
        logger.info(f"Reply Result: {reply}")
        return reply
    
    def run_rational_reply(
        self,
        dialogue_history: list[dict[str, str]],
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            input_analysis=self.state["input_analysis"],
            knowledge=self.state["knowledge"],
            information_gap=self.state["information_gap"],
            ccs_score=self.state["ccs_score"],
        )
        rational_reply = self.model.chat(
            prompt=RATIONAL_REPLY_PROMPT.format_map(format_args),
            json_format=True,
        )
        # TODO: 这里可能会出现解析错误，增加异常处理
        logger.info(f"Rational Reply Result: {rational_reply}")
        return rational_reply

    def run_emotional_reply(
        self,
        dialogue_history: list[dict[str, str]],
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            input_analysis=self.state["input_analysis"],
            trust_state=self.state["trust_state"],
            emotion_state=self.state["emotion_state"],
            ess_score=self.state["ess_score"],
            pas_score=self.state["pas_score"],
        )
        emotional_reply = self.model.chat(
            prompt=EMOTIONAL_REPLY_PROMPT.format_map(format_args),
            json_format=True,
        )
        # TODO: 这里可能会出现解析错误，增加异常处理
        logger.info(f"Emotional Reply Result: {emotional_reply}")
        return emotional_reply

    def respond(
        self, dialogue_history: list[dict[str, str]]
    ) -> dict[str, int | str | list[str]]:
        # 首先经过思考
        last_status = self.status
        if last_status == "rational":
            rational_cot = self.run_rational_cot(dialogue_history)
            self.status = rational_cot.get("status", last_status)
            if self.status == "emotional":
                logger.info("Switching to emotional state based on rational CoT analysis.")
            self.update_state(rational_cot)
        else:
            emotional_cot = self.run_emotional_cot(dialogue_history)
            self.status = emotional_cot.get("status", last_status)
            if self.status == "rational":
                logger.info("Switching to rational state based on emotional CoT analysis.")
            self.update_state(emotional_cot)
        
        # reply = self.run_reply(dialogue_history, last_status, self.status)

        # TODO: 这里应该根据 status 是否变化，来决定以怎样的风格进行回复，分四类情况

        if self.status == "rational":
            reply = self.run_rational_reply(dialogue_history)
            self.update_state(reply)
            for k in self.keypoints.keys():
                if k in reply and len(reply[k]) > 0 and reply[k] != "空" and reply[k] not in self.keypoints[k]:
                    self.keypoints[k].append(reply[k])

            response = {
                "status": self.status,
                "keypoints": copy.deepcopy(self.keypoints),
                **self.state,
                "pas_analysis": reply.get("pas_analysis", ""),
                "decision": "continue",
                "response": reply.get("response", ""),
            }
        else:
            reply = self.run_emotional_reply(dialogue_history)
            self.update_state(reply)
            response = {
                "status": self.status,
                "keypoints": copy.deepcopy(self.keypoints),
                **self.state,
                "pas_analysis": reply.get("pas_analysis", ""),
                "decision": "continue",
                "response": reply.get("response", ""),
            }

        logger.info(f"Patient Response: {response}")
        return response
