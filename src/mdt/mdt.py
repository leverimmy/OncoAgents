from src.backend import get_client


class MDT:
    def __init__(self, model_name: str, examination_data: dict[str, str]):
        self.model_name = model_name
        self.model = get_client(model_name)
        self.examination_data = examination_data

    async def respond(self, diagnosis_data: dict[str, str],
        dialogue_history: dict[str, str],
        analysis: str,
        strategy: str
    ) -> str:
        # 需要根据 strategy 里的内容，判断要引入：
        # -   examination report 的 explanation
        # -   medical guidelines / knowledge
        return ""
        pass
