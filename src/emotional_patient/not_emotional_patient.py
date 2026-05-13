from time import sleep

from src.backend import LanguageModel
from src.prompt import NOT_EMOTIONAL_REPLY_PROMPT
from src.utils import SafeDict, logger


class NotEmotionalPatient:
    def __init__(self, user_profile: str, model_name: str, url: str | None = None):
        self.user_profile = user_profile
        self.model_name = model_name
        self.model = LanguageModel(model_name=model_name, url=url)
        self.state = {
            "pas_score": 0,
        }
    
    def update_state(self, current_state: dict[str, str]) -> None:
        for key in self.state.keys():
            if key in current_state:
                self.state[key] = current_state[key]

    def run_reply(self, dialogue_history: dict[str, str]) -> dict[str, str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            dialogue_history=dialogue_history,
        )
        reply = self.model.chat(
            prompt=NOT_EMOTIONAL_REPLY_PROMPT.format_map(format_args),
            json_format=True,
        )
        if "response" not in reply:
            raise ValueError(f"LLM output missing 'response' field: {reply}")
        if "pas_score" not in reply:
            raise ValueError(f"LLM output missing 'pas_score' field: {reply}")
        logger.info(f"Reply Result: {reply}")
        return reply

    def respond(
        self,
        dialogue_history: list[dict[str, str]],
    ) -> dict[str, int | str | list[str]]:
        cnt = 0
        while True:
            cnt += 1
            try:
                reply = self.run_reply(dialogue_history)
                self.update_state(reply)
                return reply
            except Exception as e:
                logger.error(f"Error in NotEmotionalPatient respond: {e}")
                if cnt >= 5:
                    return {
                        "pas_analysis": "LLM调用失败，无法分析患者依从度",
                        "pas_score": 0,
                        "response": "很抱歉，我现在无法给出明确的回复。",
                    }
                logger.info(f"Retrying LLM call, sleep time: {2 ** cnt - 1} seconds")
                sleep(2 ** cnt - 1)
