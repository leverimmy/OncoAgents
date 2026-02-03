from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QuoteReason(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    quote: str = Field(..., description="对话中的直接短引用（建议≤25字）", max_length=200)
    reason: str = Field(..., description="为何该引用支持该维度评分，如果评分高，则说明优点；如果评分低，则说明缺点", max_length=500)


class ContradictionOrDrift(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    issue: str = Field(..., description="人设矛盾/漂移的问题描述", max_length=300)
    quote: str = Field(..., description="能体现该问题的对话引用", max_length=200)
    why_problematic: str = Field(..., description="为何这构成人设不一致或不合理", max_length=500)


class DimensionScoreWithEvidencePersonaAdherence(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    personality_score: float = Field(..., ge=0, le=5, description="性格特点一致性评分（0-5）")
    communication_style_score: float = Field(..., ge=0, le=5, description="沟通风格一致性评分（0-5）")
    education_level_score: float = Field(..., ge=0, le=5, description="教育水平体现评分（0-5）")
    financial_status_score: float = Field(..., ge=0, le=5, description="经济状况体现评分（0-5）")
    cross_turn_consistency_score: float = Field(..., ge=0, le=5, description="跨轮次稳定性评分（0-5）")
    diagnosis_context_fit_score: float = Field(..., ge=0, le=5, description="诊疗语境适配评分（0-5）")

    personality_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="性格特点一致性维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    communication_style_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="沟通风格一致性维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    education_level_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="教育水平体现维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    financial_status_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="经济状况体现维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    cross_turn_consistency_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="跨轮次稳定性维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    diagnosis_context_fit_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="诊疗语境适配维度的 1-2 条引用证据及理由（证据不足需说明）",
    )

# =========================
# 1) Persona Adherence Judge
# =========================
class JUDGE_PATIENT_JSON_SCHEMA_persona(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    overall_score: float = Field(..., ge=0, le=5, description="总体评分（0-5）")

    dimension_scores: DimensionScoreWithEvidencePersonaAdherence = Field(
        ...,
        description="各维度评分及对应证据",
    )

    contradictions_or_drift: list[ContradictionOrDrift] = Field(
        ...,
        default_factory=list,
        description="发现的人设矛盾/漂移点（没有则空列表）",
        max_length=50,
    )

    missing_signals: list[str] = Field(
        ...,
        default_factory=list,
        description="对话中完全没体现但在 patient_data 中设定的关键点（没有则空列表）",
        max_length=50,
    )

    suggestions: list[str] = Field(
        ...,
        default_factory=list,
        description="改进建议（最多 3 条更好）",
        max_length=10,
    )


# =========================
# 2) Human-likeness Judge
# =========================
class DimensionScoresHumanLikeness(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    emotional_realism: float = Field(..., ge=0, le=5, description="情绪真实度（0-5）：有合理情绪波动/担忧/缓解/防御等，并与情境匹配。")
    conversational_realism: float = Field(..., ge=0, le=5, description="沟通行为真实度（0-5）：自然出现会打断/追问/跑题/表达含糊等真实特征。")
    cognition_uncertainty: float = Field(..., ge=0, le=5, description="认知与不确定性（0-5）：呈现普通人的理解偏差、犹豫、需要解释，而非“完美理性”。")
    coping_diversity: float = Field(..., ge=0, le=5, description="应对方式多样性（0-5）：自然出现多种回复方式，例如回避、寻求安慰、讨价还价、依赖权威等。")
    personhood_coherence: float = Field(..., ge=0, le=5, description="连贯性与人味（0-5）：说话是否像一个具体的人，或是经过训练后的标准病人，而不是“角色设定说明书”。")
    low_ai_trace: float = Field(..., ge=0, le=5, description="拟真程度（0-5）：0=AI痕迹很重，越不拟真；5=几乎看不出AI痕迹，非常拟真。（注意这是反向维度，分越高，表示效果越好）")

    emotional_realism_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="情绪真实度维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    conversational_realism_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="沟通行为真实度维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    cognition_uncertainty_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="认知与不确定性维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    coping_diversity_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="应对方式多样性维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    personhood_coherence_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="连贯性与人味维度的 1-2 条引用证据及理由（证据不足需说明）",
    )
    low_ai_trace_evidence: list[QuoteReason] = Field(
        ...,
        default_factory=list,
        description="拟真程度维度的 1-2 条引用证据及理由（证据不足需说明）",
    )


class JUDGE_PATIENT_JSON_SCHEMA_humanlikeness(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 严格：不允许额外字段

    overall_score: float = Field(..., ge=0, le=5, description="总体评分（0-5）")

    dimension_scores: DimensionScoresHumanLikeness = Field(
        ...,
        description="各维度评分",
    )

    missed_opportunities: list[str] = Field(
        ...,
        default_factory=list,
        description="如果更像真人，可能会出现但没出现的行为/情绪/提问",
        max_length=50,
    )

    suggestions: list[str] = Field(
        ...,
        default_factory=list,
        description="改进建议（最多 3 条更好）",
        max_length=10,
    )
