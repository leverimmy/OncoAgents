from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import BaseAgentEvent

from src.backend import get_client
from src.json_schema import MDT_JSON_SCHEMA
from src.mdt.rag_module import get_persistent_memory
from src.prompt import MDT_PROMPT, MDT_SYSTEM_MESSAGE
from src.utils import logger

chief_expert_memory = get_persistent_memory("chief_expert")


class MDT:
    def __init__(self, model_name: str, examination_data: dict[str, str]):
        self.model_name = model_name
        self.client = get_client(model_name)
        self.agent = AssistantAgent(
            name="mdt_agent",
            model_client=self.client,
            tools=[],
            system_message=MDT_SYSTEM_MESSAGE,
            reflect_on_tool_use=True,
            max_tool_iterations=5,
            # model_client_stream=True,
            memory=[chief_expert_memory],
            output_content_type=MDT_JSON_SCHEMA,
        )
        self.examination_data = examination_data

    async def respond(
        self,
        diagnosis_data: dict[str, str],
        dialogue_history: dict[str, str],
        analysis: str,
        strategy: str
    ) -> str:
        prompt = MDT_PROMPT.format(
            diagnosis_data=diagnosis_data,
            dialogue_history=dialogue_history,
            examination_data=self.examination_data,
            analysis=analysis,
            strategy=strategy,
        )
        response = await self.agent.run(task=prompt)
        events = []
        for message in response.messages:
            if isinstance(message, BaseAgentEvent):
                events.append(message)
        for event in events:
            for i, memory_content in enumerate(event.content):
                metadata = memory_content.metadata
                source = metadata.get("source", "N/A")
                score = metadata.get("score", "N/A")
                id = metadata.get("id", "N/A")
                content = memory_content.content
                logger.info(f"Memory Content [{i}]: source = {source} | score = {score} | id = {id}\n{content}")
        return response.messages[-1].content
