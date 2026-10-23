import re
import time
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from core.llm import RETRY_DELAYS, get_llm, as_text
from core.prompts import (
    BULLETS_SYSTEM,
    CORE_SYSTEM,
    build_bullets_prompt,
    build_core_prompt,
)
from core.schemas import Analysis, BulletFix, MissingSkill, ScoreBreakdown, SkillMatch


class AnalysisError(Exception):
    """Raised when the analysis could not be produced after all retries."""


class _Core(BaseModel):
    score_breakdown: ScoreBreakdown
    matched_skills: list[SkillMatch]
    missing_skills: list[MissingSkill]
    missing_keywords: list[str]
    summary: str


class _Bullets(BaseModel):
    bullet_fixes: list[BulletFix]


def _extract_json(text: str) -> str:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start:end + 1]
    return text


def _generate(model_cls, system: str, user: str, max_attempts: int = 4, timeout: int = 120):
    llm = get_llm(0, timeout=timeout)
    messages = [("system", system), ("human", user)]
    last_error = None

    for attempt in range(1, max_attempts + 1):
        raw = ""
        try:
            raw = "".join(as_text(chunk) for chunk in llm.stream(messages))
            if not raw.strip():
                raise ValueError("empty response")
            return model_cls.model_validate_json(_extract_json(raw))
        except ValueError as e:  # bad JSON or schema validation failure
            last_error = e
            if raw.strip():
                messages = messages + [
                    ("ai", raw),
                    ("human", f"That output was invalid: {str(e)[:500]}\n"
                              "Return the corrected JSON object only."),
                ]
            else:
                time.sleep(RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)])
        except Exception as e:  # timeouts, 5xx, rate limits
            last_error = e
            time.sleep(RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)])

    raise AnalysisError(f"Analysis failed after {max_attempts} attempts: {last_error}")


def analyze(resume: str, jd: str, max_attempts: int = 4) -> Analysis:
    with ThreadPoolExecutor(max_workers=2) as pool:
        core_future = pool.submit(
            _generate, _Core, CORE_SYSTEM, build_core_prompt(resume, jd), max_attempts
        )
        bullets_future = pool.submit(
            _generate, _Bullets, BULLETS_SYSTEM, build_bullets_prompt(resume, jd), max_attempts
        )
        core = core_future.result()  # required: raises AnalysisError on failure
        try:
            bullet_fixes = bullets_future.result().bullet_fixes
        except AnalysisError as e:
            print(f"Warning: bullet rewrites unavailable ({e})")
            bullet_fixes = []

    return Analysis(**core.model_dump(), bullet_fixes=bullet_fixes)