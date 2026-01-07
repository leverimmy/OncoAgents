from pydantic import BaseModel, Field
from typing import Literal


class STRATEGY_JSON_SCHEMA(BaseModel):
    analysis: str = Field(
        description="对当前对话语境的分析，包含患者的需求、顾虑、情绪、认知等方面内容"
    )
    strategy: str = Field(
        description="根据当前对话语境生成的医生回复策略，内容要具体可操作，且符合当前对话语境"
    )


class TOM_REASONING_JSON_SCHEMA(BaseModel):
    stage: Literal[
        "认知与邀请阶段", "知识传递阶段", "共情支持阶段", "策略与总结阶段"
    ] = Field(description="判断患者和医生的对话当前处在哪个阶段")
    patient_analysis: str = Field(description="分析 Patient 的内心想法和情绪状态")
