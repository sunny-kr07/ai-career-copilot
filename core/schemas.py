from typing import Literal

from pydantic import BaseModel, Field

# Weights for the overall score. Must add up to 1.0.
SCORE_WEIGHTS = {
    "required_skills": 0.40,
    "experience_level": 0.25,
    "domain_relevance": 0.20,
    "keywords": 0.15,
}


class SkillMatch(BaseModel):
    skill: str = Field(description="Skill name as written in the job description")
    evidence: str = Field(
        description="Short snippet copied verbatim from the resume that proves this skill"
    )


class MissingSkill(BaseModel):
    skill: str = Field(description="Skill required by the job but not shown in the resume")
    importance: Literal["required", "preferred"] = Field(
        description="'required' only if the job description clearly demands it"
    )
    suggestion: str = Field(
        description="One practical way the candidate could address this gap"
    )


class BulletFix(BaseModel):
    original: str = Field(description="The resume bullet exactly as written")
    improved: str = Field(
        description="Stronger rewrite using only facts from the resume. "
        "Use a placeholder like [X%] where a metric is missing."
    )
    reason: str = Field(description="Why the rewrite is stronger, in one sentence")
    needs_user_input: bool = Field(
        description="True if the improved bullet contains a [placeholder] the user must fill in"
    )


class ScoreBreakdown(BaseModel):
    required_skills: int = Field(
        ge=0, le=100, description="How well the resume covers the required skills"
    )
    experience_level: int = Field(
        ge=0, le=100, description="Fit of seniority and years of experience"
    )
    domain_relevance: int = Field(
        ge=0, le=100, description="Relevance of past industry and project domains"
    )
    keywords: int = Field(
        ge=0, le=100, description="Coverage of important terms from the job description"
    )

    def overall(self) -> int:
        total = sum(getattr(self, name) * weight for name, weight in SCORE_WEIGHTS.items())
        return round(total)


class Analysis(BaseModel):
    score_breakdown: ScoreBreakdown
    matched_skills: list[SkillMatch]
    missing_skills: list[MissingSkill]
    missing_keywords: list[str] = Field(
        description="Important terms from the job description absent from the resume"
    )
    bullet_fixes: list[BulletFix]
    summary: str = Field(description="Two or three sentence honest overall assessment")

    @property
    def overall_score(self) -> int:
        return self.score_breakdown.overall()