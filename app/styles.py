import re

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --logo: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='3.5 6 100 100'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%23818CF8'/%3E%3Cstop offset='1' stop-color='%2322D3EE'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath fill='url(%23g)' fill-rule='evenodd' d='M23 22H54A34 34 0 1 1 30 32L22.5 27Q19 24.5 23 22Z M80 56A26 26 0 1 0 28 56A26 26 0 1 0 80 56Z'/%3E%3Cellipse cx='50.5' cy='56' rx='8.4' ry='11.2' fill='url(%23g)'/%3E%3Cellipse cx='68' cy='57.5' rx='5.6' ry='7.8' fill='url(%23g)'/%3E%3C/svg%3E");
  --bg: #0B0D12;        --surface: #11141B;   --raised: #161A23;   --hover: #1B2030;
  --line: #232836;      --line-strong: #2E3547;
  --ink: #E6E8EE;       --ink-2: #B4BACA;     --muted: #8B93A7;
  --brand: #6366F1;     --brand-hi: #7C7FF5;  --brand-soft: rgba(99,102,241,.14);
  --cyan: #22D3EE;      --cyan-soft: rgba(34,211,238,.12);
  --ok: #34D399;        --ok-soft: rgba(52,211,153,.10);    --ok-line: rgba(52,211,153,.28);
  --bad: #F87171;       --bad-soft: rgba(248,113,113,.10);  --bad-line: rgba(248,113,113,.28);
  --warn: #FBBF24;      --warn-soft: rgba(251,191,36,.10);  --warn-line: rgba(251,191,36,.28);
  --r-sm: 8px; --r-md: 10px; --r-lg: 14px;
}

/* Inter on text only. Never target span/div globally: Streamlit icons are spans that
   rely on the Material Symbols ligature font, and overriding it prints "arrow_down" etc. */
.stApp, .stApp :where(p, h1, h2, h3, h4, h5, h6, li, label, a, button, input, textarea,
  [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"]),
.hero, .hero *, .card, .card *, .stat, .stat *, .skill, .skill *, .bcard, .bcard *,
.status, .status *, .step, .step *, .brand, .brand-sub, .section-title, .section-title *,
.section-sub, .h2, .muted, .chip, .ring, .ring * , .bar-row, .bar-row * {
  font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
}
/* belt and braces: force the icon font back on anything Streamlit marks as an icon */
[data-testid="stIconMaterial"], [data-testid="stIconMaterial"] *,
[class*="material-symbols"], [class*="material-icons"], [class*="MaterialIcon"] {
  font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
  font-feature-settings: "liga" 1; letter-spacing: normal; text-transform: none;
}
.stApp { background: var(--bg); color: var(--ink); -webkit-font-smoothing: antialiased; }
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1080px; }
hr { border-color: var(--line) !important; }
/* focus: one soft indigo ring per control, never a second inner outline */
:focus-visible { outline: none; }
button:focus-visible, a:focus-visible, [role="tab"]:focus-visible {
  outline: 2px solid var(--brand-hi) !important; outline-offset: 2px; }

/* sidebar */
section[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

/* buttons */
.stButton > button, .stDownloadButton > button {
  width: 100%; border-radius: var(--r-md); font-weight: 500; font-size: .92rem; padding: .5rem 1rem;
  background: var(--raised); color: var(--ink); border: 1px solid var(--line);
  transition: background-color .12s ease, border-color .12s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--hover); border-color: var(--line-strong); color: var(--ink);
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
  background: var(--brand); border-color: var(--brand); color: #fff; font-weight: 600;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
  background: var(--brand-hi); border-color: var(--brand-hi); color: #fff;
}
.stButton > button:disabled { background: var(--surface); color: var(--muted); border-color: var(--line); opacity: .7; }

/* inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div {
  background: var(--surface) !important; border: 1px solid var(--line) !important;
  border-radius: var(--r-md) !important; color: var(--ink) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--brand) !important; box-shadow: 0 0 0 3px var(--brand-soft) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stCheckbox label { color: var(--ink-2) !important; font-size: .88rem; }
[data-testid="stFileUploaderDropzone"] {
  background: var(--surface); border: 1px dashed var(--line-strong); border-radius: var(--r-lg);
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--brand); }

/* expander, alerts, status, code */
[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: var(--r-lg); background: var(--surface); }
[data-testid="stExpander"] summary { font-weight: 600; }
[data-testid="stAlert"] { border-radius: var(--r-md); }
[data-testid="stStatus"] { border: 1px solid var(--line); border-radius: var(--r-lg); background: var(--surface); }
pre, code { border-radius: var(--r-sm) !important; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { height: 44px; padding: 0 14px; font-weight: 500; color: var(--muted); }
.stTabs [data-baseweb="tab"]:hover { color: var(--ink); }
.stTabs [aria-selected="true"] { color: var(--ink); font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--brand); height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* header */
.hero { position: relative; display: flex; align-items: center; gap: 18px; padding: 10px 0 28px;
  margin-bottom: 1.6rem; border-bottom: 1px solid var(--line); isolation: isolate; }
.hero::before { content: ""; position: absolute; z-index: -1; left: -40px; top: -60px; width: 460px; height: 220px;
  background: radial-gradient(closest-side, rgba(99,102,241,.22), rgba(34,211,238,.06) 60%, transparent);
  filter: blur(8px); pointer-events: none; }
.hero::after { content: ""; position: absolute; left: 0; bottom: -1px; width: 120px; height: 2px;
  background: linear-gradient(90deg, var(--brand), var(--cyan)); }
.hero-mark { flex: none; width: 58px; height: 58px; border-radius: 16px; position: relative;
  background: var(--logo) center / 66% no-repeat,
              linear-gradient(145deg, #1A1F2E 0%, #0F121A 100%);
  border: 1px solid var(--line-strong);
  box-shadow: 0 0 0 1px rgba(255,255,255,.03) inset, 0 10px 30px rgba(99,102,241,.30), 0 0 22px rgba(34,211,238,.10); }
.hero-title { font-size: 2.5rem; font-weight: 700; letter-spacing: -0.035em; line-height: 1.1;
  background: linear-gradient(135deg, #FFFFFF 35%, #A5B4FC 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; color: transparent; }
.hero-sub { font-size: 1rem; color: var(--muted); margin-top: 8px; line-height: 1.5; white-space: nowrap; }

/* section headings */
.section-title { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 1rem; margin: 2px 0 6px; }
.section-title .num { background: var(--brand-soft); color: var(--brand-hi); border: 1px solid rgba(99,102,241,.35);
  width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center;
  justify-content: center; font-size: .78rem; font-weight: 600; }
.section-sub { color: var(--muted); font-size: .88rem; margin: 0 0 10px; line-height: 1.45; }
.h2 { font-size: 1.15rem; font-weight: 600; letter-spacing: -0.01em; margin: 6px 0 2px; }
.muted { color: var(--muted); font-size: .88rem; line-height: 1.5; }

/* cards */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
  padding: 18px 20px; height: 100%; }
.card.center { text-align: center; }

/* feature cards: restrained glass over a soft indigo/cyan glow */
.feature-grid { position: relative; isolation: isolate; display: grid; gap: 16px; align-items: stretch;
  grid-template-columns: repeat(4, minmax(0, 1fr)); }
.feature-grid::before { content: ""; position: absolute; z-index: -1; inset: -36px -12px; pointer-events: none;
  background:
    radial-gradient(240px 140px at 14% 30%, rgba(99,102,241,.34), transparent 70%),
    radial-gradient(260px 150px at 84% 70%, rgba(34,211,238,.22), transparent 70%),
    radial-gradient(220px 120px at 52% 10%, rgba(124,127,245,.14), transparent 70%);
  filter: blur(14px); }
.card.feature { position: relative; overflow: hidden; height: auto; min-height: 148px; padding: 18px 18px 20px;
  background: linear-gradient(160deg, rgba(255,255,255,.075) 0%, rgba(255,255,255,.025) 100%);
  -webkit-backdrop-filter: blur(16px) saturate(150%); backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255,255,255,.09);
  box-shadow: 0 1px 0 rgba(255,255,255,.07) inset, 0 12px 28px rgba(0,0,0,.35);
  transition: transform .18s ease, border-color .18s ease, background-color .18s ease; }
.card.feature::before { content: ""; position: absolute; left: 14%; right: 14%; top: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(165,180,252,.75), rgba(34,211,238,.55), transparent); }
.card.feature:hover { transform: translateY(-2px); border-color: rgba(165,180,252,.32); }
.f-ico { width: 36px; height: 36px; border-radius: 10px; margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(99,102,241,.32), rgba(34,211,238,.14));
  border: 1px solid rgba(255,255,255,.12); box-shadow: 0 0 18px rgba(99,102,241,.25);
  background-position: center; background-repeat: no-repeat; background-size: 19px; }
.f-ico.i-target { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23A5B4FC' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='8.5'/%3E%3Ccircle cx='12' cy='12' r='4.5'/%3E%3Ccircle cx='12' cy='12' r='.8' fill='%23A5B4FC'/%3E%3C/svg%3E"); }
.f-ico.i-list { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23A5B4FC' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 6.5h11M9 12h11M9 17.5h11'/%3E%3Cpath d='M3.8 6.5l1 1 2-2M3.8 12l1 1 2-2M3.8 17.5l1 1 2-2'/%3E%3C/svg%3E"); }
.f-ico.i-spark { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23A5B4FC' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3.5l1.9 5.1 5.1 1.9-5.1 1.9L12 17.5l-1.9-5.1L5 10.5l5.1-1.9z'/%3E%3Cpath d='M18.5 16.5v3M17 18h3'/%3E%3C/svg%3E"); }
.f-ico.i-chat { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23A5B4FC' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4.5 6.5A2.5 2.5 0 0 1 7 4h10a2.5 2.5 0 0 1 2.5 2.5v7A2.5 2.5 0 0 1 17 16H11l-4.5 3.5V16H7a2.5 2.5 0 0 1-2.5-2.5z'/%3E%3C/svg%3E"); }
.card.feature .card-title { font-size: .96rem; font-weight: 600; color: var(--ink); margin-bottom: 6px; }
.card.feature .muted { font-size: .86rem; line-height: 1.55; color: var(--ink-2); opacity: .8; }
@media (max-width: 900px) { .feature-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .feature-grid { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { .card.feature:hover { transform: none; } }
.card-title { font-weight: 600; font-size: .88rem; color: var(--ink-2); margin-bottom: 8px; }
.summary { font-size: .96rem; line-height: 1.6; color: var(--ink); }

/* score ring */
.ring { --p: 0; --c: #6366F1; width: 148px; height: 148px; border-radius: 50%; margin: 6px auto 12px;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), var(--line) 0);
  display: flex; align-items: center; justify-content: center; }
.ring-in { width: 120px; height: 120px; border-radius: 50%; background: var(--surface);
  display: flex; flex-direction: column; align-items: center; justify-content: center; }
.ring-num { font-size: 2.6rem; font-weight: 700; line-height: 1; letter-spacing: -0.03em; font-variant-numeric: tabular-nums; }
.ring-sub { font-size: .75rem; color: var(--muted); margin-top: 3px; }
.ring-label { font-weight: 600; font-size: 1rem; }

/* bars */
.bar-row { margin: 12px 0; }
.bar-top { display: flex; justify-content: space-between; font-size: .88rem; font-weight: 500; margin-bottom: 6px; }
.bar-top .muted { font-weight: 400; font-size: .8rem; font-variant-numeric: tabular-nums; }
.bar { background: var(--line); border-radius: 999px; height: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; }

/* stat tiles */
.stat { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-md); padding: 14px 16px; }
.stat-label { color: var(--muted); font-size: .8rem; font-weight: 500; }
.stat-value { font-size: 1.6rem; font-weight: 700; line-height: 1.25; letter-spacing: -0.02em; margin-top: 2px;
  font-variant-numeric: tabular-nums; }
.stat-hint { color: var(--muted); font-size: .78rem; margin-top: 2px; }

/* skills */
.skill { border-radius: var(--r-md); padding: 10px 14px; margin-bottom: 8px; border: 1px solid transparent; }
.skill.ok { background: var(--ok-soft); border-color: var(--ok-line); }
.skill.miss { background: var(--bad-soft); border-color: var(--bad-line); }
.skill-name { font-weight: 600; font-size: .92rem; }
.skill.ok .skill-name { color: var(--ok); }
.skill.miss .skill-name { color: var(--bad); }
.skill-sub { color: var(--ink-2); font-size: .85rem; margin-top: 4px; line-height: 1.5; }
.badge { font-size: .68rem; font-weight: 600; border-radius: 999px; padding: 2px 8px; margin-left: 6px; vertical-align: middle; }
.badge.req { background: var(--bad-soft); color: var(--bad); border: 1px solid var(--bad-line); }
.badge.pref { background: var(--raised); color: var(--muted); border: 1px solid var(--line-strong); }

/* chips */
.chip { display: inline-block; border-radius: 999px; padding: 4px 12px; margin: 0 6px 6px 0; font-size: .84rem;
  font-weight: 500; background: var(--brand-soft); color: var(--brand-hi); border: 1px solid rgba(99,102,241,.3); }
.chip.miss { background: var(--cyan-soft); color: var(--cyan); border-color: rgba(34,211,238,.28); }

/* bullet rewrites */
.bcard { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); padding: 14px 18px; margin-bottom: 12px; }
.blabel { font-size: .78rem; font-weight: 600; color: var(--muted); margin: 10px 0 4px; }
.orig { color: var(--muted); text-decoration: line-through; text-decoration-color: var(--line-strong); line-height: 1.5; }
.impr { background: var(--ok-soft); border-left: 3px solid var(--ok); border-radius: 0 var(--r-sm) var(--r-sm) 0;
  padding: 8px 12px; font-weight: 500; line-height: 1.5; }
.ph { background: var(--warn-soft); color: var(--warn); font-weight: 600; border-radius: 4px; padding: 0 4px; border: 1px solid var(--warn-line); }
.why { color: var(--muted); font-size: .85rem; margin-top: 10px; line-height: 1.5; }
.note { color: var(--warn); font-size: .8rem; margin-top: 6px; }

/* status boxes */
.status { border-radius: var(--r-md); padding: 10px 14px; margin: 6px 0; border: 1px solid; }
.status.ok { background: var(--ok-soft); border-color: var(--ok-line); }
.status.warn { background: var(--warn-soft); border-color: var(--warn-line); }
.status-title { font-weight: 600; font-size: .9rem; }
.status-detail { color: var(--muted); font-size: .82rem; margin-top: 2px; }

/* sidebar progress */
.brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.05rem;
  letter-spacing: -0.015em; margin-bottom: 4px; }
.brand-mark { flex: none; width: 30px; height: 30px; border-radius: 9px;
  background: var(--logo) center / 68% no-repeat, linear-gradient(145deg, #1A1F2E 0%, #0F121A 100%);
  border: 1px solid var(--line-strong); box-shadow: 0 4px 14px rgba(99,102,241,.28); }
.brand-sub { color: var(--muted); font-size: .8rem; margin-bottom: 16px; padding-left: 40px; }
.step { display: flex; align-items: center; gap: 10px; padding: 5px 0; font-size: .9rem; color: var(--muted); }
.step .dot { width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid var(--line-strong);
  display: inline-flex; align-items: center; justify-content: center; font-size: .65rem; font-weight: 700; color: var(--bg); }
.step.done { color: var(--ink); font-weight: 500; }
.step.done .dot { background: var(--cyan); border-color: var(--cyan); }

/* chat */
[data-testid="stChatMessage"] { border-radius: var(--r-lg); background: var(--surface); border: 1px solid var(--line); }
[data-testid="stChatInput"] { border-radius: var(--r-md); }
[data-testid="stChatMessageAvatarUser"] { background: var(--raised); color: var(--ink-2); border: 1px solid var(--line-strong); border-radius: var(--r-sm); }
[data-testid="stChatMessageAvatarAssistant"] { background: var(--brand-soft); color: var(--brand-hi); border: 1px solid rgba(99,102,241,.35); border-radius: var(--r-sm); }

/* chat input: a single container carries the border and the focus ring */
[data-testid="stChatInput"] {
  background: var(--surface) !important; border: 1px solid var(--line) !important;
  border-radius: var(--r-lg) !important; box-shadow: none !important;
  transition: border-color .12s ease, box-shadow .12s ease;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--brand) !important; box-shadow: 0 0 0 3px var(--brand-soft) !important;
}
[data-testid="stChatInput"] *, [data-testid="stChatInput"] *:focus, [data-testid="stChatInput"] *:focus-visible {
  outline: none !important; box-shadow: none !important;
}
[data-testid="stChatInput"] [data-baseweb], [data-testid="stChatInput"] textarea {
  background: transparent !important; border: none !important;
}
[data-testid="stChatInput"] button { background: var(--brand) !important; color: #fff !important; border-radius: var(--r-sm) !important; }
[data-testid="stChatInput"] button:disabled { background: var(--raised) !important; color: var(--muted) !important; }

/* select: same single ring, no inner bar */
.stSelectbox [data-baseweb="select"] > div:focus-within {
  border-color: var(--brand) !important; box-shadow: 0 0 0 3px var(--brand-soft) !important;
}
.stSelectbox [data-baseweb="select"] *, .stSelectbox [data-baseweb="select"] *:focus,
.stSelectbox [data-baseweb="select"] *:focus-visible { outline: none !important; }
.stSelectbox [data-baseweb="select"] svg { color: var(--muted); }

/* dropdown list */
[data-baseweb="popover"] > div { background: var(--surface) !important; border: 1px solid var(--line-strong);
  border-radius: var(--r-md) !important; box-shadow: 0 12px 32px rgba(0,0,0,.45) !important; overflow: hidden; }
[data-baseweb="popover"] ul { background: var(--surface) !important; padding: 4px !important; }
[data-baseweb="popover"] li { background: transparent !important; color: var(--ink-2) !important;
  border-radius: var(--r-sm) !important; font-size: .9rem; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {
  background: var(--brand-soft) !important; color: var(--ink) !important; }

@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
@media (max-width: 820px) { .hero-sub { white-space: normal; } }
@media (max-width: 640px) { .hero-title { font-size: 1.6rem; } .hero-mark { width: 40px; height: 40px; border-radius: 12px; }  .block-container { padding-top: 1.2rem; } }
</style>
"""

CSS = re.sub(r"\n\s*\n", "\n", CSS)
