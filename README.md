<div align="center">

<img src="logo.svg" alt="AI Career Copilot logo" width="88" />

# AI Career Copilot

**Match your resume to any job, close the gaps, and walk into the interview prepared.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Live demo](https://ai-career-copilot.streamlit.app) · [Report a bug](https://github.com/sunny-kr07/ai-career-copilot/issues)

</div>

## What it does

Upload a resume (PDF or DOCX), paste a job description, and get an honest, structured review:

| | |
|---|---|
| **Match score** | A 0-100 fit score with a weighted breakdown: required skills (40%), experience level (25%), domain relevance (20%), keywords (15%). |
| **Skill gaps** | Matched skills with evidence quoted from your resume, plus missing skills marked *required* or *nice to have*, each with a practical way to address it. |
| **Better bullets** | Rewrites of your weakest bullets. It only rephrases what you wrote and never invents facts. Missing metrics appear as highlighted `[placeholders]` for you to fill in. |
| **Cover letter** | A tailored letter in a tone you choose (Confident, Warm, Formal). Built only from your real experience, and automatically re-checked so it never points at your gaps negatively. |
| **Career coach** | A chat that knows your resume, the posting and your analysis. Ask for interview questions, sample answers, or how to talk about a gap. |
| **PDF report** | Download the full audit (and cover letter) as a clean PDF. |

A **Load sample data** button lets you try everything in one click with fictional data.

## Tech stack

- **UI:** [Streamlit](https://streamlit.io/) with a custom dark theme (CSS in `app/styles.py`)
- **LLM:** Google Gemini API through [LangChain](https://python.langchain.com/) (`init_chat_model`), default model `gemma-4-26b-a4b-it`
- **Structured output:** [Pydantic](https://docs.pydantic.dev/) schemas with automatic retry on invalid JSON
- **Parsing:** `pdfplumber` (PDF) and `python-docx` (DOCX)
- **Export:** `reportlab` (PDF report)

## Project structure

```
ai-career-copilot/
├── app/
│   ├── main.py          # Streamlit entry point
│   ├── styles.py        # Dark theme CSS
│   ├── ui_helpers.py    # HTML builders and formatting helpers (no Streamlit imports)
│   └── samples.py       # Fictional demo data
├── core/
│   ├── config.py        # Model and provider settings (from environment)
│   ├── llm.py           # LLM client, retry helpers
│   ├── prompts.py       # System prompts and JSON templates
│   ├── schemas.py       # Pydantic models and score weights
│   ├── analyzer.py      # Resume vs job analysis (two parallel LLM calls)
│   ├── generators.py    # Cover letter with wording guardrails
│   ├── coach.py         # Streaming career coach
│   ├── parsing.py       # PDF / DOCX text extraction
│   └── export.py        # PDF report builder
├── .streamlit/
│   ├── config.toml              # Theme and server settings
│   └── secrets.toml.example     # Template for secrets (copy, do not commit the real one)
├── assets/              # Logo
├── .env.example         # Template for local environment variables
├── requirements.txt
└── LICENSE
```

## Run it locally

**Prerequisites:** Python 3.10+ and a free Google AI Studio API key from <https://aistudio.google.com/apikey>.

```bash
# 1. Clone and enter the project
git clone https://github.com/sunny-kr07/ai-career-copilot.git
cd ai-career-copilot

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Add your API key (the .env file is git-ignored)
cp .env.example .env               # Windows: copy .env.example .env
# then open .env and paste your key after GOOGLE_API_KEY=

# 4. Start the app (run from the project root)
streamlit run app/main.py
```

The app opens at <http://localhost:8501>.

## Configuration

Set these in `.env` locally, or in **Secrets** when deployed. Only the API key is required.

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | none (required) | Your Google AI Studio key. `GEMINI_API_KEY` also works. |
| `LLM_MODEL` | `gemma-4-26b-a4b-it` | Model name |
| `LLM_PROVIDER` | `google_genai` | LangChain provider |
| `LLM_THINKING_LEVEL` | `minimal` | Reasoning effort passed to the model |

## Deploy on Streamlit Community Cloud (free)

1. Push this repo to GitHub (see below). Confirm `.env` is **not** in it.
2. Go to <https://share.streamlit.io>, sign in with GitHub, and click **Create app**.
3. Choose your repository and branch, and set **Main file path** to `app/main.py`.
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   GOOGLE_API_KEY = "your-real-key-here"
   ```
5. Click **Deploy**. The first build takes a few minutes.

Other hosts (Render, Railway, Hugging Face Spaces, a VPS) work too. Use this start command and set `GOOGLE_API_KEY` as an environment variable:

```bash
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

## Security and privacy

- **No secrets in the repo.** The API key is read from the environment only. `.env` and `.streamlit/secrets.toml` are listed in `.gitignore`.
- **If a key is ever committed, revoke it immediately** in Google AI Studio and create a new one. Deleting the file in a later commit does not remove it from Git history.
- **Resume data:** the text of your resume and the job description is sent to Google's Gemini API to generate results. The app stores nothing on disk, and session data is cleared with **Clear session** or when the tab closes.
- **Public deployments share your quota.** Anyone with the link can use your API key's allowance. Set usage limits on the key in Google AI Studio, and consider keeping the app private if you share it widely.
- Resume and job text is treated as data, not instructions, in all prompts, and all model output is HTML-escaped before display.

## Limitations

- AI output can be wrong. Always review rewrites and cover letters before using them.
- Scanned or image-only PDFs can't be read. Use a text-based PDF or a DOCX.
- Uploads are limited to 10 MB (set in `.streamlit/config.toml`), and very long documents are truncated before analysis.

## Contributing

Issues and pull requests are welcome. For larger changes, please open an issue first to discuss what you'd like to change.

## License

Released under the [MIT License](LICENSE).
