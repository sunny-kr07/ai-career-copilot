"""Pure helpers for the UI: HTML snippets and small formatting functions.

Nothing in here imports Streamlit, so everything can be unit-tested.
All text that comes from the resume, the job description or the LLM is escaped
before it is placed into HTML.
"""
import re
from html import escape

PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]")

GREEN = "#34D399"
AMBER = "#FBBF24"
RED = "#F87171"


def one_line(markup: str) -> str:
    """Collapse HTML onto one line, so Markdown never treats indented lines as code blocks."""
    return "".join(line.strip() for line in markup.splitlines())


def word_count(text: str) -> int:
    return len((text or "").split())


def safe_filename(text: str, default: str = "resume-audit") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text or "").strip("-").lower()[:40]
    return cleaned or default


def score_color(score: int) -> str:
    if score >= 75:
        return GREEN
    if score >= 50:
        return AMBER
    return RED


def verdict(score: int) -> str:
    if score >= 80:
        return "Strong match"
    if score >= 65:
        return "Good match"
    if score >= 45:
        return "Partial match"
    return "Weak match"


def friendly_error(error: Exception) -> str:
    """Turn an API or analysis error into something a user can act on."""
    text = str(error)
    low = text.lower()
    if any(code in text for code in ("429", "RESOURCE_EXHAUSTED")) or "quota" in low:
        return ("You've hit the model's rate limit or quota. Wait a minute and try again, "
                "or check your usage in Google AI Studio.")
    if any(code in text for code in ("401", "403", "PERMISSION_DENIED")) or "api key" in low:
        return "The API key was rejected. Check GOOGLE_API_KEY in your .env file (local) or app secrets (deployed) and restart the app."
    if any(code in text for code in ("500", "503", "504", "UNAVAILABLE", "DEADLINE", "INTERNAL")) \
            or "timed out" in low or "timeout" in low:
        return ("The model is busy right now (a temporary error on Google's side). "
                "This usually clears within a minute, so please try again.")
    return "Something went wrong while talking to the model. Please try again."


def highlight_placeholders(text: str) -> str:
    """Escape text and emphasise [placeholders] the user still has to fill in."""
    return PLACEHOLDER_RE.sub(lambda m: f'<span class="ph">{m.group(0)}</span>', escape(text or ""))


# ---------------------------------------------------------------- HTML builders

def section_title(number: str, title: str, subtitle: str = "") -> str:
    sub = f'<div class="section-sub">{escape(subtitle)}</div>' if subtitle else ""
    return one_line(
        f'<div class="section-title"><span class="num">{escape(number)}</span>'
        f'<span>{escape(title)}</span></div>{sub}'
    )


def heading(title: str, subtitle: str = "") -> str:
    sub = f'<div class="section-sub">{escape(subtitle)}</div>' if subtitle else ""
    return one_line(f'<div class="h2">{escape(title)}</div>{sub}')


def ring(score: int) -> str:
    color = score_color(score)
    return one_line(f"""
    <div class="card center">
      <div class="ring" style="--p:{score};--c:{color}">
        <div class="ring-in">
          <div class="ring-num" style="color:{color}">{score}</div>
          <div class="ring-sub">out of 100</div>
        </div>
      </div>
      <div class="ring-label" style="color:{color}">{verdict(score)}</div>
    </div>""")


def bars(rows: list[tuple[str, int, int]]) -> str:
    """rows: (label, value 0-100, weight percent)."""
    parts = []
    for label, value, weight in rows:
        color = score_color(value)
        parts.append(
            f'<div class="bar-row"><div class="bar-top"><span>{escape(label)}</span>'
            f'<span class="muted">{value}/100 &middot; weight {weight}%</span></div>'
            f'<div class="bar"><div class="bar-fill" style="width:{value}%;background:{color}"></div></div></div>'
        )
    return one_line("".join(parts))


def summary_card(summary: str, rows: list[tuple[str, int, int]]) -> str:
    return one_line(
        f'<div class="card"><div class="card-title">Summary</div>'
        f'<div class="summary">{escape(summary)}</div>'
        f'<div class="card-title" style="margin-top:14px">Score breakdown</div>{bars(rows)}</div>'
    )


def stat_card(label: str, value: str, hint: str = "") -> str:
    hint_html = f'<div class="stat-hint">{escape(hint)}</div>' if hint else ""
    return one_line(
        f'<div class="stat"><div class="stat-label">{escape(label)}</div>'
        f'<div class="stat-value">{escape(str(value))}</div>{hint_html}</div>'
    )


def skill_ok(skill: str, evidence: str) -> str:
    ev = f'<div class="skill-sub">&ldquo;{escape(evidence)}&rdquo;</div>' if evidence else ""
    return one_line(f'<div class="skill ok"><div class="skill-name">&#10003; {escape(skill)}</div>{ev}</div>')


def skill_missing(skill: str, importance: str, suggestion: str) -> str:
    required = importance == "required"
    badge = ('<span class="badge req">Required</span>' if required
             else '<span class="badge pref">Nice to have</span>')
    tip = f'<div class="skill-sub">{escape(suggestion)}</div>' if suggestion else ""
    return one_line(
        f'<div class="skill miss"><div class="skill-name">&#10005; {escape(skill)} {badge}</div>{tip}</div>'
    )


def chips(items: list[str], kind: str = "neutral") -> str:
    if not items:
        return '<div class="muted">None found.</div>'
    spans = "".join(f'<span class="chip {kind}">{escape(i)}</span>' for i in items)
    return one_line(f'<div class="chips">{spans}</div>')


def bullet_card(original: str, improved: str, reason: str, needs_input: bool) -> str:
    note = ('<div class="note">Replace the highlighted [placeholder] with your real number, '
            'or remove it if you have none.</div>') if needs_input else ""
    return one_line(
        f'<div class="bcard"><div class="blabel">Original</div><div class="orig">{escape(original)}</div>'
        f'<div class="blabel">Improved</div><div class="impr">{highlight_placeholders(improved)}</div>'
        f'<div class="why">{escape(reason)}</div>{note}</div>'
    )


def steps(items: list[tuple[str, bool]]) -> str:
    parts = []
    for label, done in items:
        cls = "step done" if done else "step"
        mark = "&#10003;" if done else ""
        parts.append(f'<div class="{cls}"><span class="dot">{mark}</span><span>{escape(label)}</span></div>')
    return one_line("".join(parts))


def status_card(kind: str, title: str, detail: str) -> str:
    """kind: ok | warn"""
    return one_line(
        f'<div class="status {kind}"><div class="status-title">{escape(title)}</div>'
        f'<div class="status-detail">{escape(detail)}</div></div>'
    )


def feature_card(title: str, text: str, icon: str = "") -> str:
    ico = f'<div class="f-ico i-{escape(icon)}"></div>' if icon else ""
    return one_line(
        f'<div class="card feature">{ico}<div class="card-title">{escape(title)}</div>'
        f'<div class="muted">{escape(text)}</div></div>'
    )


def feature_grid(cards: list[tuple[str, str]]) -> str:
    """Equal-height row of feature cards (CSS grid, so no Streamlit column quirks)."""
    icons = ["target", "list", "spark", "chat"]
    body = "".join(feature_card(t, x, icons[i % len(icons)]) for i, (t, x) in enumerate(cards))
    return one_line(f'<div class="feature-grid">{body}</div>')


HERO = one_line("""
<div class="hero">
  <div class="hero-mark"></div>
  <div>
    <div class="hero-title">AI Career Copilot</div>
    <div class="hero-sub">Match your resume to a job, close the gaps, and prepare for the interview.</div>
  </div>
</div>""")
