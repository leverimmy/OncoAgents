from pydantic import BaseModel, Field
from typing import Literal


class RATIONAL_JSON_SCHEMA_STAGE0(BaseModel):
    input_analysis: str = Field(description="对当前输入进行分析")

class RATIONAL_JSON_SCHEMA_STAGE1(BaseModel):
    input_analysis: str = Field(description="对当前输入进行分析")
    knowledge: str = Field(description="对当前疾病掌握的相关知识")
    gap_analysis: str = Field(description="当前存在的信息差距分析")
    information_gap: str = Field(description="当前存在的信息差距")
    ccs_score: int = Field(ge=0, le=100, description=" 患者对病情严重性、治疗逻辑、以及“不治疗的后果”的真实理解程度评分，0-100分")

class RATIONAL_JSON_SCHEMA_STAGE2(BaseModel):
    input_analysis: str = Field(description="对当前输入进行分析")
    knowledge: str = Field(description="对当前疾病掌握的相关知识")
    gap_analysis: str = Field(description="当前存在的信息差距分析")
    information_gap: str = Field(description="当前存在的信息差距")
    ccs_score: int = Field(ge=0, le=100, description=" 患者对病情严重性、治疗逻辑、以及“不治疗的后果”的真实理解程度评分，0-100分")

class RATIONAL_JSON_SCHEMA_STAGE3(BaseModel):
    input_analysis: str = Field(description="对当前输入进行分析")
    knowledge: str = Field(description="对当前疾病掌握的相关知识")
    gap_analysis: str = Field(description="当前存在的信息差距分析")
    information_gap: str = Field(description="当前存在的信息差距")
    ccs_score: int = Field(ge=0, le=100, description=" 患者对病情严重性、治疗逻辑、以及“不治疗的后果”的真实理解程度评分，0-100分")

class EMOTIONAL_JSON_SCHEMA(BaseModel):
    emotional_analysis: str = Field(description="对当前情绪进行分析")
    emotion_state: str = Field(description="当前情绪状态描述")
    ess_score: int = Field(ge=0, le=100, description="情绪压力度，0-100分")

class REPLY_JSON_SCHEMA(BaseModel):
    stage_analysis: str = Field(description="对状态转移的分析")
    stage_transfer: Literal["认知与邀请阶段", "知识传递阶段", "共情支持阶段", "决策与总结阶段"] = Field(
        description="接下来转移到的阶段，只能为 认知与邀请阶段 / 知识传递阶段 / 共情支持阶段 / 决策与总结阶段"
    )
    pas_analysis: str = Field(description="对当前情况的患者依从度分析")
    pas_score: int = Field(ge=0, le=100, description="患者依从度，0-100分")
    stage_analysis: str = Field(description="当前阶段分析")
    decision: Literal["continue", "accept", "reject"] = Field(
        description="决策，只能为 continue / accept / reject"
    )
    response: str = Field(description="作为患者，处于当前阶段的情绪和认知状态，表达适当的内容")

# All
RATIONAL_JSON_SCHEMAS = [RATIONAL_JSON_SCHEMA_STAGE0,
                         RATIONAL_JSON_SCHEMA_STAGE1,
                         RATIONAL_JSON_SCHEMA_STAGE2,
                         RATIONAL_JSON_SCHEMA_STAGE3]
