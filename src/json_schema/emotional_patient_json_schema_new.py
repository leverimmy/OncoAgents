from typing import Literal

from pydantic import BaseModel, Field


class RATIONAL_JSON_SCHEMA(BaseModel):
    input_analysis: str = Field(description="对当前输入进行分析")
    knowledge: str = Field(description="对当前疾病掌握的相关知识")
    gap_analysis: str = Field(description="当前存在的信息差距分析")
    information_gap: str = Field(description="当前存在的信息差距")
    ccs_score: int = Field(
        ge=0,
        le=100,
        description="患者对病情严重性、治疗逻辑、以及“不治疗的后果”的真实理解程度评分，0-100分",
    )
    

class EMOTIONAL_JSON_SCHEMA(BaseModel):
    emotion_analysis: str = Field(description="对当前情绪进行分析")
    emotion_state: str = Field(description="当前情绪状态描述")
    trust_analysis: str = Field(description="对当前医生的信任状态的分析")
    trust_state: str = Field(description="对当前医生的信任状态")
    ess_score: int = Field(ge=0, le=100, description="情绪压力度，0-100分")


class REPLY_JSON_SCHEMA(BaseModel):
    pas_analysis: str = Field(description="对当前情况的患者依从度分析")
    pas_score: int = Field(ge=0, le=100, description="患者依从度，0-100分")
    decision: Literal["continue", "accept", "reject"] = Field(
        description="决策，只能为 continue / accept / reject"
    )
    response: str = Field(
        description="作为患者，处于当前阶段的情绪和认知状态，表达适当的内容"
    )
