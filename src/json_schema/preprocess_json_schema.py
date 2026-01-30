from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field, ConfigDict


class SYMPTOM_JSON_SCHEMA(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    chief_complaint: str = Field(..., description="主诉")
    additional_symptom: str = Field("", description="伴随症状/补充症状（可填“无”）")
    symptom_duration: str = Field(..., description="症状持续时间")

class PERSONAL_HISTORY_JSON_SCHEMA(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    smoking_status: str = Field(..., description="吸烟史描述")
    alcohol_use: str = Field(..., description="饮酒史描述")

class AuxiliaryExaminationItem(BaseModel):
    check_type: str = Field(..., description="检查类型，如CT/MR/病理/基因检测等")
    item: str = Field(..., description="检查项目/部位/取材等")
    result: str = Field(..., description="检查结果原文/描述")

class AUXILIARY_EXAMINATION_JSON_SCHEMA(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    auxiliary_examination: List[AuxiliaryExaminationItem] = Field(
        ..., description="辅助检查列表"
    )

class DIAGNOSIS_JSON_SCHEMA(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    diagnosis: str = Field(..., description="诊断结果内容")

class TREATMENT_JSON_SCHEMA(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    treatment: str = Field(..., description="治疗方案内容")

class ADDITONAL_INFO_JSON_SCHEMA(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段
    
    chief_complaint: str = Field(..., description="主诉")
    additional_symptom: str = Field("", description="伴随症状/补充症状（可填“无”）")
    symptom_duration: str = Field(..., description="症状持续时间")

    diagnosis: str = Field(..., description="诊断结果内容")

    treatment: str = Field(..., description="治疗方案内容")

    auxiliary_examination: List[AuxiliaryExaminationItem] = Field(
        ..., description="辅助检查列表"
    )
