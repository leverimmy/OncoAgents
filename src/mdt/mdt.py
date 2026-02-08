from src.backend import LanguageModel
from src.mdt.ragtool import hybrid_search_answer
from src.prompt import MDT_PROMPT
from src.utils import SafeDict


class MDT:
    def __init__(self, model_name: str, url: str | None, examination_data: dict[str, str]):
        self.model_name = model_name
        self.model = LanguageModel(model_name=model_name, url=url)
        self.examination_data = examination_data

    def respond(
        self,
        keywords: list[str],
    ) -> list[dict[str, str]]:
        
        if len(keywords) > 3:
            keywords = keywords[:3]
        pairs = []
        for keyword in keywords:
            pairs.append({
                "query": keyword,
                "answer": hybrid_search_answer(keyword),
            })

        for pair in pairs:
            explanation_args = SafeDict(
                query=pair["query"],
                examination_data=self.examination_data,
                answer=pair["answer"],
            )
            explanation = self.model.chat(
                prompt=MDT_PROMPT.format_map(explanation_args),
                json_format=False,
            )
            pair["explanation"] = explanation
        
        return [{
            "query": pair["query"],
            "explanation": pair["explanation"],
        } for pair in pairs]
