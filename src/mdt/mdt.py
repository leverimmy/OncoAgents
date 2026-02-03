import json

from autogen_agentchat.messages import UserMessage

from src.backend import get_client
from src.json_schema import MDT_JSON_SCHEMA, QUERY_JSON_SCHEMA
from src.mdt.ragtool import hybrid_search_answer
from src.prompt import MDT_PROMPT, QUERY_PROMPT


class MDT:
    def __init__(self, model_name: str, examination_data: dict[str, str]):
        self.model_name = model_name
        self.client = get_client(model_name)
        self.examination_data = examination_data

    async def respond(
        self,
        diagnosis_data: dict[str, str],
        dialogue_history: dict[str, str],
        analysis: str,
        strategy: str
    ) -> list[dict[str, str]]:
        query_prompt = QUERY_PROMPT.format(
            diagnosis_data=diagnosis_data,
            dialogue_history=dialogue_history,
            examination_data=self.examination_data,
            analysis=analysis,
            strategy=strategy,
        )
        keywords = await self.client.create(
            messages=[UserMessage(content=query_prompt, source="User")],
            json_output=QUERY_JSON_SCHEMA,
        )
        json_result = json.loads(keywords.content)

        answers = []
        for keyword in json_result["items"]:
            answers.append({
                "query": keyword,
                "answer": hybrid_search_answer(keyword),
            })
        
        prompt = MDT_PROMPT.format(
            diagnosis_data=diagnosis_data,
            dialogue_history=dialogue_history,
            examination_data=self.examination_data,
            analysis=analysis,
            strategy=strategy,
            results=answers,
        )

        queries = await self.client.create(
            messages=[UserMessage(content=prompt, source="User")],
            json_output=MDT_JSON_SCHEMA,
        )

        return json.loads(queries.content)
