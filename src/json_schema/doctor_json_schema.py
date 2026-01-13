from typing import Literal

from pydantic import BaseModel, Field


class STRATEGY_JSON_SCHEMA(BaseModel):
    analysis: str = Field(
        description="对当前对话语境的分析，包含患者的认知、需求、顾虑、情绪等方面内容"
    )
    strategy: str = Field(
        description="根据当前对话语境生成的医生回复策略，内容要具体可操作，且符合当前对话语境"
    )
    is_explanation_needed: bool = Field(
        description="是否需要引用外部医学知识来解释诊断结果或治疗方案"
    )


class TOM_REASONING_JSON_SCHEMA(BaseModel):
    stage: Literal[
        "认知与邀请阶段", "知识传递阶段", "共情支持阶段", "策略与总结阶段"
    ] = Field(description="判断患者和医生的对话当前处在哪个阶段")
    patient_analysis: str = Field(description="分析 Patient 的理性认知和情绪状态")
