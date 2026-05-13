from src.backend import LanguageModel
from src.prompt.simple_emotional_patient_prompt import (
    COT_PROMPTS,
    REPLY_PROMPTS,
)
from src.utils import (
    NAME2STAGE,
    STAGE2NAME,
    STAGE_E,
    STAGE_K,
    STAGE_PI,
    STAGE_S,
    SafeDict,
    logger,
)


class SimpleEmotionalPatient:
    def __init__(self, user_profile: str, model_name: str, url: str | None = None):
        self.user_profile = user_profile
        self.model_name = model_name
        self.model = LanguageModel(model_name=model_name, url=url)

        self.stage = STAGE_PI

        self.state = {
            "ccs_score": 0,
            "ess_score": 50,
            "pas_score": 50,
        }

    def update_state(self, cot: dict[str, str]) -> None:
        for key in self.state.keys():
            if key in cot:
                self.state[key] = cot[key]
    
    def run_cot(
        self,
        dialogue_history: list[dict[str, str]],
        stage: int,
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
        )
        result = self.model.chat(
            prompt=COT_PROMPTS[stage].format_map(format_args),
            json_format=True,
        )
        logger.info(f"CoT@Stage {STAGE2NAME[stage]} Result: {result}")
        return result
    
    def run_reply(
        self,
        dialogue_history: list[dict[str, str]],
        last_stage: int,
        current_stage: int,
    ) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,

            ccs_score=self.state["ccs_score"],
            ess_score=self.state["ess_score"],
            pas_score=self.state["pas_score"],
        )

        if last_stage == STAGE_PI and current_stage == STAGE_K:
            logger.info("Switching from PI to K stage.")
        elif last_stage == STAGE_K and current_stage == STAGE_K:
            logger.info("Remaining in K stage.")
        elif last_stage == STAGE_K and current_stage == STAGE_E:
            logger.info("Switching from K to E stage.")
        elif last_stage == STAGE_K and current_stage == STAGE_S:
            logger.info("Switching from K to S stage.")
        elif last_stage == STAGE_E and current_stage == STAGE_E:
            logger.info("Remaining in E stage.")
        elif last_stage == STAGE_E and current_stage == STAGE_K:
            logger.info("Switching from E to K stage.")
        elif last_stage == STAGE_E and current_stage == STAGE_S:
            logger.info("Switching from E to S stage.")
        elif last_stage == STAGE_S and current_stage == STAGE_S:
            logger.info("Remaining in S stage.")

        reply = self.model.chat(
            prompt=REPLY_PROMPTS[last_stage][current_stage].format_map(format_args),
            json_format=True,
        )
        logger.info(f"Reply Result: {reply}")
        return reply
    
    def respond(
        self, dialogue_history: list[dict[str, str]]
    ) -> dict[str, int | str | list[str]]:
        # respond 分两部分

        # 第一部分通过对话来判断状态应当如何转移
        last_stage = self.stage
        if self.state["ess_score"] >= 80:
            self.stage = STAGE_E
        else:
            cot = self.run_cot(dialogue_history, last_stage)
            if "stage" in cot:
                self.stage = NAME2STAGE[cot["stage"]]

        # 第二部分根据状态的转移来生成回复内容以及指标变化
        reply = self.run_reply(
            dialogue_history,
            last_stage=last_stage,
            current_stage=self.stage,
        )

        self.update_state(reply)

        response = {
            "stage": STAGE2NAME[self.stage],
            **reply,
        }

        logger.info(f"Patient Response: {response}")
        return response

if __name__ == '__main__':
    patient = SimpleEmotionalPatient(
        user_profile="患者，女性，45岁，已婚，有两个孩子，职业是教师。",
        model_name="Qwen/Qwen3-8B",
        url="http://localhost:8000/v1",
    )

    dialogue_history = []
    while True:
        input_text = input("请输入医生的发言（输入exit退出）：")
        if input_text.lower() == "exit":
            break
        dialogue_history.append({"role": "doctor", "content": input_text})
        response = patient.respond(dialogue_history)
        print(f"患者回复：{response['response']}")
        dialogue_history.append({"role": "patient", "content": response["response"]})
    