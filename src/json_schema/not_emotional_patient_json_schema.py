from typing import Literal

from pydantic import BaseModel, Field


class NOT_EMOTIONAL_REPLY_JSON_SCHEMA(BaseModel):
    pas_analysis: str = Field(description="对当前情况的患者依从度分析")
    pas_score: int = Field(ge=0, le=100, description="患者依从度，0-100分")
    decision: Literal["continue", "accept", "reject"] = Field(
        description="决策，只能为 continue / accept / reject"
    )
    response: str = Field(description="作为患者，处于当前阶段认知状态，表达适当的内容")
