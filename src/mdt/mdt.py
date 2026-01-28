from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import BaseAgentEvent, UserMessage
from autogen_core.memory import MemoryQueryResult

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
            # tools=[self.explain_item],
            system_message=MDT_SYSTEM_MESSAGE,
            reflect_on_tool_use=True,
            max_tool_iterations=5,
            # model_client_stream=True,
            # memory=[chief_expert_memory],
            output_content_type=MDT_JSON_SCHEMA,
        )
        self.examination_data = examination_data
    
    async def explain_item(self, item: str, obs: str) -> MemoryQueryResult:
        """
        给定检查项目和检查结果，返回外部知识库中相关的专业资料。

        Args:
            item (str): 需要解释的检查项目名称。
            obs (str): 检查结果描述。

        Returns:
            MemoryQueryResult: 包含相关解释的记忆查询结果。
        """
        query = await self.client.create(
            messages=[
                UserMessage(
                    content=f"你是一位资深的医疗专家。请根据以下检查项目和检查结果，转化为一句 RAG 查询语句，去外部知识库中寻找相关的专业解释。\
                        \n\n检查项目: {item}\n检查结果: {obs}",
                    source="User",
                )
            ],
        )
        print(f"Query: {query.content}")
        return await chief_expert_memory.query(
            # query=f"项目:{item}\n\n检查结果:{obs}"
            query=query.content
        )

    async def respond(
        self,
        diagnosis_data: dict[str, str],
        dialogue_history: dict[str, str],
        analysis: str,
        strategy: str
    ) -> list[dict[str, str]]:
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
        return response.messages[-1].content.to_json()
