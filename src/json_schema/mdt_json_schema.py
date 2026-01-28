from pydantic import BaseModel, Field
from typing import List


class MDTItem(BaseModel):
    item: str = Field(..., description="需要解释的检查项目名称")
    explanation: str = Field(..., description="对该检查项目结果的详细解释")

    def __init__(self, item: str, explanation: str):
        super().__init__(item=item, explanation=explanation)
    
    def to_json(self) -> dict[str, str]:
        return {
            "item": self.item,
            "explanation": self.explanation,
        }

class MDT_JSON_SCHEMA(BaseModel):
    items: List[MDTItem] = Field(
        default_factory=list,
        description="本轮需要解释的检查项目及其解释列表（可为空）",
    )

    def __init__(self, items: list[dict[str, str]] = []):
        super().__init__(
            items=[MDTItem(**item) for item in items]
        )

    def to_json(self) -> list[dict[str, str]]:
        return [item.to_json() for item in self.items]
