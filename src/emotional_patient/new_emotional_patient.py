from concurrent.futures import ThreadPoolExecutor

from src.backend import LanguageModel
from src.prompt import (
    EMOTIONAL_PROMPT,
    RATIONAL_PROMPT,
    REFINE_PROMPT,
    REPLY_PROMPT,
)
from src.utils import SafeDict, logger


class NewEmotionalPatient:
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

        self.state = {
            "knowledge": [],
            "information_gap": [],
            "trust_state": "",
            "emotion_state": "",
            "ccs_score": 0,
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
            prompt=RATIONAL_PROMPT.format_map(format_args),
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
            prompt=EMOTIONAL_PROMPT.format_map(format_args),
            json_format=True,
        )
        # TODO: 这里可能会出现解析错误，增加异常处理
        logger.info(f"Emotional CoT Result: {emotional_cot}")
        return emotional_cot

    def run_refine_cot(
        self,
        dialogue_history: list[dict[str, str]],
        rational_cot: dict[str, str],
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            emotion_state=self.state["emotion_state"],
            ess_score=self.state["ess_score"],

            input_analysis=rational_cot.get("input_analysis", ""),
            knowledge=rational_cot.get("knowledge", []),
            gap_analysis=rational_cot.get("gap_analysis", ""),
            information_gap=rational_cot.get("information_gap", []),
            ccs_score=rational_cot.get("ccs_score", ""),
        )
        refine_cot = self.model.chat(
            prompt=REFINE_PROMPT.format_map(format_args),
            json_format=True,
        )

        for key in self.keypoints.keys():
            if len(refine_cot.get(key, "")) > 0 and refine_cot.get(key, "空") != "空" and refine_cot[key] not in self.keypoints[key]:
                self.keypoints[key].append(refine_cot[key])
        # TODO: 这里可能会出现解析错误，增加异常处理
        logger.info(f"Refine CoT Result: {refine_cot}")
        return refine_cot
    
    def run_reply(
        self, dialogue_history: list[dict[str, str]], current_state: dict[str, str]
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
            input_analysis=current_state.get("input_analysis", ""),
            knowledge=current_state.get("knowledge", []),
            information_gap=current_state.get("information_gap", []),
            ccs_score=current_state.get("ccs_score", ""),
            trust_state=current_state.get("trust_state", ""),
            emotion_state=current_state.get("emotion_state", ""),
            ess_score=current_state.get("ess_score", ""),
            pas_score=self.state["pas_score"],
        )
        reply = self.model.chat(
            prompt=REPLY_PROMPT.format_map(format_args),
            json_format=True,
        )
        # TODO: 这里可能会出现解析错误，增加异常处理
        logger.info(f"Reply Result: {reply}")
        return reply

    def respond(
        self, dialogue_history: list[dict[str, str]]
    ) -> dict[str, int | str | list[str]]:
        
        # 并行运行 rational_cot 和 emotional_cot
        with ThreadPoolExecutor(max_workers=2) as executor:
            rational_future = executor.submit(
                self.run_rational_cot, dialogue_history
            )
            emotional_future = executor.submit(
                self.run_emotional_cot, dialogue_history
            )

            rational_cot = rational_future.result()
            emotional_cot = emotional_future.result()

        self.update_state(emotional_cot)
        self.update_state(rational_cot)
        refine_cot = self.run_refine_cot(dialogue_history, rational_cot)
        self.update_state(refine_cot)

        cot = {
            **emotional_cot,
            **refine_cot,
            "original": rational_cot,
        }  # 合并三个 CoT 的结果，供生成回复使用

        # 运行 run_reply 生成回复
        try:
            reply = self.run_reply(dialogue_history, cot)
            cot.update(reply)
            self.update_state(cot)
            logger.info(f"Current Patient State: {cot}")
            return cot
        except Exception as e:
            logger.error(f"Error in EmotionalPatient respond: {e}")
            return {}
