import re

from core.llm import get_llm, as_text, invoke_with_retry
from core.schemas import Analysis

COVER_SYSTEM = """You write concise, professional cover letters for job applications.

Truthfulness rules (most important):
- Use ONLY facts stated in the resume. Never invent employers, numbers, tools, achievements
  or responsibilities.
- Never describe the candidate's experience more strongly than the resume does. If the resume
  says "worked with Docker", write "worked with Docker", not "extensive experience with Docker".
- Do not add outcomes or qualities the resume doesn't state (for example "seamless user
  experiences", "robust architecture", "high-traffic", "proven track record", "scalable").
- Do not use "expert", "expertise" or "proficient" unless the resume itself does.
- Do not attribute requirements to the job description that it doesn't state. Only refer to
  requirements that actually appear in it.
- Keep numbers exactly as written in the resume.

Handling skill gaps (positive wording only):
- Never write what the candidate hasn't done or lacks. Never use "not", "no experience",
  "haven't", "lack" or "limited" in connection with any skill.
- For one important missing skill, write at most one positive sentence that builds on adjacent
  experience from the resume, for example: "I'm keen to build on my experience with
  [adjacent skill from the resume] by growing into [missing skill]."
- Never claim any experience with the missing skill.

Format:
- Plain text, no markdown. Start with "Dear Hiring Manager," and end with "Sincerely," followed
  by the candidate's name. Do not put a name or address block at the top.
- Three or four short paragraphs, 150 to 300 words. If the resume doesn't support that length
  honestly, write a shorter letter. Never pad with unsupported claims.
- Take the candidate's name from the resume; if it isn't there, use [Your Name].
- Take the company and role from the job description; if the company isn't named, use [Company].
- Open with a specific hook tied to the role. Don't start with "I am writing to express my interest".
- Lead with the strongest matched skills and concrete achievements from the resume.
- Close with a specific, confident call to action.
- Return only the letter text."""

# Wording that points at a gap. Matched against the lowercase letter.
FORBIDDEN_PATTERNS = [
    r"\bnot (yet )?(worked|used|had|done)\b",
    r"\bno (direct |hands-on |formal |prior )?experience\b",
    r"\bhaven't\b",
    r"\bhave not\b",
    r"\black(s|ed|ing)?\b",
    r"\blimited (experience|exposure)\b",
    r"\bunfamiliar\b",
    r"\bnew to\b",
]


def find_violations(letter: str) -> list[str]:
    low = letter.lower()
    found = []
    for pattern in FORBIDDEN_PATTERNS:
        match = re.search(pattern, low)
        if match:
            found.append(match.group(0))
    return found


def cover_letter(resume: str, jd: str, analysis: Analysis,
                 tone: str = "confident", max_attempts: int = 3) -> str:
    matched = ", ".join(s.skill for s in analysis.matched_skills) or "none identified"
    gaps = ", ".join(
        s.skill for s in analysis.missing_skills if s.importance == "required"
    ) or "none"

    prompt = (
        f"Tone: {tone}\n"
        f"Matched skills (emphasize these): {matched}\n"
        f"Required skills missing from the resume (never claim these, never mention "
        f"them negatively): {gaps}\n\n"
        f"<resume>\n{resume}\n</resume>\n\n"
        f"<job_description>\n{jd}\n</job_description>"
    )

    llm = get_llm(0.5, timeout=120)
    messages = [("system", COVER_SYSTEM), ("human", prompt)]
    letter = ""
    for _ in range(max_attempts):
        letter = as_text(invoke_with_retry(llm, messages)).strip()
        bad = find_violations(letter)
        if not bad:
            return letter
        messages = messages + [
            ("ai", letter),
            ("human", f"Rewrite the letter. It contains forbidden wording: {', '.join(bad)}. "
                      "Remove every mention of what the candidate hasn't done or lacks. "
                      "For a missing skill, use only a positive sentence about building on "
                      "adjacent experience. Keep everything else. Return only the letter."),
        ]
    return letter  # best effort after retries; the caller can still run find_violations