from pydantic import BaseModel, Field
from typing import Literal

class NOT_EMOTIONAL_REPLY_JSON_SCHEMA(BaseModel):
    tas_analysis: str = Field(description="对当前治疗方案的接受度分析")
    tas_score: int = Field(ge=0, le=100, description="接受度评分，0-100分")
    decision: Literal["continue", "accept", "reject"] = Field(
        description="决策，只能为 continue / accept / reject"
    )
    response: str = Field(description="作为患者，处于当前阶段认知状态，表达适当的内容")
