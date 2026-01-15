from pydantic import BaseModel, Field
from typing import List


class MDTItem(BaseModel):
    item: str = Field(..., description="需要解释的检查项目名称")
    explanation: str = Field(..., description="对该检查项目结果的详细解释")


class MDT_JSON_SCHEMA(BaseModel):
    items: List[MDTItem] = Field(
        default_factory=list,
        description="本轮需要解释的检查项目及其解释列表（可为空）",
    )
