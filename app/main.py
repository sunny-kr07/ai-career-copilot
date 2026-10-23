"""AI Career Copilot - Streamlit UI.  Run from the project root:  streamlit run app/main.py"""
import hashlib
import os
import sys
import time
from pathlib import Path

# Make `core` and `app` importable no matter where Streamlit is started from.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

# On Streamlit Community Cloud the API key lives in "Secrets", not in a .env file.
# Copy it into the environment BEFORE `core.config` is imported, so both work the same way.
for _name in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "LLM_MODEL", "LLM_PROVIDER", "LLM_THINKING_LEVEL"):
    try:
        if _name in st.secrets and not os.environ.get(_name):
            os.environ[_name] = str(st.secrets[_name])
    except Exception:  # no secrets configured (normal for local runs that use .env)
        break

from app import ui_helpers as ui  # noqa: E402
from app.samples import SAMPLE_JD, SAMPLE_JOB_TITLE, SAMPLE_RESUME  # noqa: E402
from app.styles import CSS  # noqa: E402
from core import config  # noqa: E402
from core.analyzer import analyze  # noqa: E402
from core.coach import CoachError, coach_stream, suggested_questions  # noqa: E402
from core.export import build_pdf  # noqa: E402
from core.generators import cover_letter, find_violations  # noqa: E402
from core.parsing import ParseError, extract_text  # noqa: E402
from core.schemas import SCORE_WEIGHTS  # noqa: E402

st.set_page_config(page_title="AI Career Copilot", page_icon="🧭", layout="wide",
                   initial_sidebar_state="expanded")

S = st.session_state
MIN_JD_CHARS = 100
SCORE_LABELS = {
    "required_skills": "Required skills",
    "experience_level": "Experience level",
    "domain_relevance": "Domain relevance",
    "keywords": "Keywords",
}
TONES = ["Confident", "Warm", "Formal"]


# ----------------------------------------------------------------------- state

def init_state() -> None:
    defaults = {
        "resume_text": None, "resume_name": None, "resume_source": None, "resume_sig": None,
        "parse_error": None, "job_title": "", "jd": "",
        "analysis": None, "analysis_key": None, "analysis_secs": None, "analysis_error": None,
        "letter_text": "", "letter_error": None, "letter_tone": TONES[0], "include_letter": False,
        "chat": [], "pending_q": None, "last_failed_q": None, "upload_nonce": 0,
    }
    for key, value in defaults.items():
        S.setdefault(key, list(value) if isinstance(value, list) else value)


def reset_all() -> None:
    nonce = S.get("upload_nonce", 0) + 1
    for key in list(S.keys()):
        del S[key]
    init_state()
    S.upload_nonce = nonce  # new key makes the file uploader forget its file


def load_sample() -> None:
    S.resume_text = SAMPLE_RESUME
    S.resume_name = "Sample resume"
    S.resume_source = "sample"
    S.resume_sig = None
    S.parse_error = None
    S.jd = SAMPLE_JD
    S.job_title = SAMPLE_JOB_TITLE
    S.upload_nonce += 1


def ask(question: str) -> None:
    S.pending_q = question


def clear_chat() -> None:
    S.chat = []
    S.last_failed_q = None


def api_key_present() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))


def inputs_key() -> str:
    raw = f"{S.resume_text or ''}\x00{(S.jd or '').strip()}"
    return hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()


def jd_ready() -> bool:
    return len((S.jd or "").strip()) >= MIN_JD_CHARS


def input_limit() -> int:
    return getattr(config, "MAX_INPUT_CHARS", 30_000)


# --------------------------------------------------------------------- sidebar

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="brand"><span class="brand-mark"></span>AI Career Copilot</div>'
                    '<div class="brand-sub">Analyze &rarr; Improve &rarr; Apply &rarr; Prepare</div>',
                    unsafe_allow_html=True)
        st.markdown(ui.steps([
            ("Resume added", bool(S.resume_text)),
            ("Job description added", jd_ready()),
            ("Fit analysis", S.analysis is not None),
            ("Cover letter", bool(S.letter_text)),
            ("Coaching chat", bool(S.chat)),
        ]), unsafe_allow_html=True)
        st.write("")
        st.button("Load sample data", on_click=load_sample, key="btn_sample",
                  help="Fills in a demo resume and job description so you can try the app.")
        st.button("Clear session", on_click=reset_all, key="btn_clear",
                  help="Removes your resume, job description and all results from this session.")
        st.divider()
        if api_key_present():
            st.caption(f"Model: `{config.MODEL}`")
        else:
            st.error("No API key found. Add GOOGLE_API_KEY to your .env file (local) or to the app secrets (deployed), then restart the app.")
        st.caption("Privacy: your resume text is sent to Google's Gemini API to generate results. "
                   "Nothing is saved to disk, and it is cleared when you press Clear session or close the tab.")


# ---------------------------------------------------------------------- inputs

def handle_upload(upload) -> None:
    if upload is not None:
        sig = (upload.name, upload.size)
        if S.resume_sig == sig:
            return
        S.resume_sig = sig
        try:
            S.resume_text = extract_text(upload.getvalue(), upload.name)
            S.resume_name, S.resume_source, S.parse_error = upload.name, "upload", None
        except ParseError as e:
            S.resume_text = S.resume_name = S.resume_source = None
            S.parse_error = str(e)
        except Exception:
            S.resume_text = S.resume_name = S.resume_source = None
            S.parse_error = "That file could not be read. Try another PDF or DOCX."
    elif S.resume_source == "upload":  # the user removed the file
        S.resume_text = S.resume_name = S.resume_source = S.resume_sig = None


def run_analysis() -> None:
    limit = input_limit()
    resume, jd = S.resume_text[:limit], S.jd.strip()[:limit]
    started = time.time()
    S.analysis_error = None
    with st.status("Analyzing your resume against the job...", expanded=True) as status:
        st.write("Reading your resume and the job description")
        st.write("Scoring skills, experience and keywords (usually 10 to 30 seconds)")
        try:
            result = analyze(resume, jd)
        except Exception as e:  # any failure becomes a friendly message
            status.update(label="Analysis failed", state="error", expanded=False)
            S.analysis_error = (ui.friendly_error(e), str(e))
            return
        status.update(label="Analysis complete", state="complete", expanded=False)
    S.analysis, S.analysis_key = result, inputs_key()
    S.analysis_secs = round(time.time() - started)
    S.letter_text, S.letter_error, S.include_letter = "", None, False
    S.chat, S.last_failed_q = [], None
    st.rerun()


def render_inputs() -> bool:
    with st.expander("Resume and job description", expanded=S.analysis is None):
        left, right = st.columns(2, gap="large")

        with left:
            st.markdown(ui.section_title("1", "Your resume", "PDF or DOCX, text-based (not a scan)"),
                        unsafe_allow_html=True)
            upload = st.file_uploader("Upload your resume", type=["pdf", "docx"],
                                      key=f"resume_up_{S.upload_nonce}", label_visibility="collapsed")
            handle_upload(upload)
            if S.resume_text:
                st.markdown(ui.status_card(
                    "ok", f"Ready: {S.resume_name}",
                    f"{ui.word_count(S.resume_text):,} words read from the file"), unsafe_allow_html=True)
                if len(S.resume_text) > input_limit():
                    st.warning(f"Your resume is very long. Only the first {input_limit():,} characters will be used.")
                if st.checkbox("Show the text we extracted", key="show_preview"):
                    st.text(S.resume_text[:4000] + ("\n..." if len(S.resume_text) > 4000 else ""))
            elif S.parse_error:
                st.error(S.parse_error)

        with right:
            st.markdown(ui.section_title("2", "Target job", "Paste the complete job posting"),
                        unsafe_allow_html=True)
            st.text_input("Job title (optional)", key="job_title", placeholder="e.g. Backend Engineer")
            st.text_area("Job description", key="jd", height=230, label_visibility="collapsed",
                         placeholder="Paste the full job description here, including requirements...")
            words = ui.word_count(S.jd)
            if words and not jd_ready():
                st.caption(f"{words} words. Paste the full posting for better results (at least {MIN_JD_CHARS} characters).")
            elif words:
                st.caption(f"{words:,} words")

        needs = []
        if not api_key_present():
            needs.append("add your API key (.env or app secrets)")
        if not S.resume_text:
            needs.append("upload your resume")
        if not jd_ready():
            needs.append("paste the job description")
        label = "Analyze my fit" if S.analysis is None else "Re-analyze"
        _, middle, _ = st.columns([1, 2, 1])
        with middle:
            clicked = st.button(label, type="primary", key="btn_analyze", disabled=bool(needs))
            if needs:
                st.caption("To continue: " + ", ".join(needs) + ".")
    return clicked


def render_analysis_error() -> None:
    if S.analysis_error:
        friendly, technical = S.analysis_error
        st.error(friendly)
        if st.checkbox("Show technical details", key="show_tech"):
            st.code(technical)


def render_empty_state() -> None:
    st.write("")
    cards = [
        ("Match score", "See how well your resume fits the job, with an honest breakdown."),
        ("Skill gaps", "Find the required skills and keywords your resume is missing."),
        ("Better bullets", "Get stronger rewrites of your weakest resume bullets, with no invented facts."),
        ("Interview coach", "Practice tough questions and learn how to address your gaps."),
    ]
    st.markdown(ui.feature_grid(cards), unsafe_allow_html=True)
    st.write("")
    st.caption("New here? Press **Load sample data** in the sidebar to try the app in one click.")


# --------------------------------------------------------------------- results

def render_overview(a) -> None:
    score = a.overall_score
    rows = [(SCORE_LABELS[k], getattr(a.score_breakdown, k), int(w * 100)) for k, w in SCORE_WEIGHTS.items()]
    required_gaps = [s for s in a.missing_skills if s.importance == "required"]
    total_skills = len(a.matched_skills) + len(a.missing_skills)

    left, right = st.columns([1, 2], gap="large")
    with left:
        st.markdown(ui.ring(score), unsafe_allow_html=True)
    with right:
        st.markdown(ui.summary_card(a.summary, rows), unsafe_allow_html=True)
    if S.analysis_secs is not None:
        st.caption(f"Analyzed in {S.analysis_secs}s. Scores are AI estimates: use them as guidance, not a verdict.")

    st.write("")
    stats = st.columns(4, gap="medium")
    tiles = [
        ("Match score", f"{score}%", ui.verdict(score)),
        ("Skills matched", f"{len(a.matched_skills)} / {total_skills}" if total_skills else "0", "found in your resume"),
        ("Required gaps", str(len(required_gaps)), "must-have skills missing"),
        ("Keywords missing", str(len(a.missing_keywords)), "worth adding if true"),
    ]
    for col, (label, value, hint) in zip(stats, tiles):
        with col:
            st.markdown(ui.stat_card(label, value, hint), unsafe_allow_html=True)

    st.write("")
    good, bad = st.columns(2, gap="large")
    with good:
        st.markdown(ui.heading("What you already show", "Skills backed by evidence in your resume"),
                    unsafe_allow_html=True)
        if a.matched_skills:
            for s in a.matched_skills:
                st.markdown(ui.skill_ok(s.skill, s.evidence), unsafe_allow_html=True)
        else:
            st.info("No matching skills were found. Check that the right resume and job were used.")
    with bad:
        st.markdown(ui.heading("Gaps to address", "Required skills are listed first"), unsafe_allow_html=True)
        ordered = sorted(a.missing_skills, key=lambda s: s.importance != "required")
        if ordered:
            for s in ordered:
                st.markdown(ui.skill_missing(s.skill, s.importance, s.suggestion), unsafe_allow_html=True)
        else:
            st.success("No gaps found for this job.")

    st.write("")
    st.markdown(ui.heading("Keywords to consider adding", "Only add terms that honestly describe your experience"),
                unsafe_allow_html=True)
    st.markdown(ui.chips(a.missing_keywords, "miss"), unsafe_allow_html=True)

    st.write("")
    st.markdown(ui.heading("Stronger bullet points", "Rewrites use only facts already in your resume"),
                unsafe_allow_html=True)
    if a.bullet_fixes:
        for b in a.bullet_fixes:
            st.markdown(ui.bullet_card(b.original, b.improved, b.reason, b.needs_user_input),
                        unsafe_allow_html=True)
        export = "\n\n".join(f"ORIGINAL: {b.original}\nIMPROVED: {b.improved}\nWHY: {b.reason}" for b in a.bullet_fixes)
        st.download_button("Download rewrites (.txt)", export, file_name="bullet-rewrites.txt",
                           mime="text/plain", key="dl_rewrites")
    else:
        st.info("No bullet rewrites were generated this time. Press Re-analyze above to try again.")


def render_letter(a) -> None:
    st.markdown(ui.heading("Cover letter", "Built from your real experience. Gaps are handled positively, never invented away."),
                unsafe_allow_html=True)
    opts, action = st.columns([2, 1], gap="large")
    with opts:
        tone = st.selectbox("Tone", TONES, key="letter_tone")
    with action:
        st.write("")
        generate = st.button("Regenerate letter" if S.letter_text else "Generate cover letter",
                             type="primary", key="btn_letter")
    if generate:
        S.letter_error = None
        with st.spinner("Writing your letter... (about 10 to 20 seconds)"):
            try:
                limit = input_limit()
                S.letter_text = cover_letter(S.resume_text[:limit], S.jd.strip()[:limit], a, tone=tone.lower())
                S.include_letter = True
            except Exception as e:
                S.letter_error = ui.friendly_error(e)
    if S.letter_error:
        st.error(S.letter_error)
    if not S.letter_text:
        st.info("Press Generate to write a first draft. You can edit it freely afterwards.")
        return

    st.text_area("Your letter (edit freely)", key="letter_text", height=400)
    words = ui.word_count(S.letter_text)
    st.caption(f"{words} words")
    flagged = find_violations(S.letter_text)
    if flagged:
        st.warning("The draft contains wording that points at a gap (" + ", ".join(flagged) +
                   "). Consider rewording it positively.")
    if "[Company]" in S.letter_text or "[Your Name]" in S.letter_text:
        st.info("Replace the bracketed placeholders, such as [Company], before sending.")
    st.caption("Always read the letter and make sure every claim is true for you.")
    st.download_button("Download .txt", S.letter_text, file_name="cover-letter.txt", mime="text/plain",
                       key="dl_letter")


def render_coach(a) -> None:
    st.markdown(ui.heading("Career coach", "Ask anything about this job. Answers use your resume, the posting and your analysis."),
                unsafe_allow_html=True)
    if not S.chat:
        st.markdown(ui.status_card("ok", "Try one of these to get started", "Or type your own question below."),
                    unsafe_allow_html=True)
        cols = st.columns(2, gap="medium")
        for i, question in enumerate(suggested_questions(a)):
            with cols[i % 2]:
                st.button(question, key=f"sq_{i}", on_click=ask, args=(question,))

    for message in S.chat:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    typed = st.chat_input("Ask about interviews, skill gaps, your projects...")
    question = typed or S.pending_q
    S.pending_q = None
    if question:
        S.last_failed_q = None
        with st.chat_message("user"):
            st.markdown(question)
        reply = None
        with st.chat_message("assistant"):
            try:
                limit = input_limit()
                reply = st.write_stream(coach_stream(S.resume_text[:limit], S.jd.strip()[:limit], a, S.chat, question))
            except CoachError as e:
                st.error(str(e))
                S.last_failed_q = question
        if reply:
            S.chat += [{"role": "user", "content": question}, {"role": "assistant", "content": reply}]
            st.rerun()

    if S.last_failed_q:
        st.button("Try that question again", key="btn_retry", on_click=ask, args=(S.last_failed_q,))
    if S.chat:
        st.button("Clear conversation", key="btn_clear_chat", on_click=clear_chat)


def render_report(a) -> None:
    st.markdown(ui.heading("PDF report", "A clean, shareable audit of this analysis."), unsafe_allow_html=True)
    st.checkbox("Include my cover letter draft (adds a page)", key="include_letter", disabled=not S.letter_text)
    try:
        pdf = build_pdf(a, job_title=(S.job_title or "").strip(),
                        cover_letter=S.letter_text if (S.include_letter and S.letter_text) else "")
    except Exception:
        st.error("The report could not be built. Please try Re-analyze and download again.")
        return
    name = ui.safe_filename(S.job_title, "resume-audit")
    st.download_button("Download PDF report", pdf, file_name=f"resume-audit-{name}.pdf", mime="application/pdf",
                       type="primary", key="dl_pdf")
    st.markdown("**Inside the report:** overall score and breakdown, matched skills with evidence, "
                "missing skills and keywords, and your bullet rewrites.")
    st.caption("The report is generated on your device's session and is not stored anywhere.")


# ------------------------------------------------------------------------ main

init_state()
st.markdown(CSS, unsafe_allow_html=True)
render_sidebar()
st.markdown(ui.HERO, unsafe_allow_html=True)
if render_inputs():
    run_analysis()  # runs outside the expander: st.status can't live inside one
render_analysis_error()

analysis = S.analysis
if analysis is None:
    render_empty_state()
else:
    if S.analysis_key != inputs_key():
        st.warning("Your resume or job description changed after this analysis. "
                   "Open the inputs above and press Re-analyze to refresh the results.")
    tab_overview, tab_letter, tab_coach, tab_report = st.tabs(
        ["Overview", "Cover letter", "Career coach", "PDF report"])
    with tab_overview:
        render_overview(analysis)
    with tab_letter:
        render_letter(analysis)
    with tab_coach:
        render_coach(analysis)
    with tab_report:
        render_report(analysis)
