from pydantic import BaseModel, Field


class RAG_TEST_JSON_SCHEMA(BaseModel):
    relevance_score: int = Field(..., ge=0, le=100, description="相关性评分，0-100 分")
    