# Semantic Kernel on Azure — Claims Validation

[![CI](https://github.com/satyajeetaiml-hue/agentic-ai-azure-semantic-kernel/actions/workflows/ci.yml/badge.svg)](https://github.com/satyajeetaiml-hue/agentic-ai-azure-semantic-kernel/actions/workflows/ci.yml)

> Companion project to the *Agentic AI on Azure — Enterprise Master Class*, showing the
> **Semantic Kernel** framework alongside the Microsoft Agent Framework labs.
> Course hub: [azure-agentic-ai-masterclass](https://github.com/satyajeetaiml-hue/azure-agentic-ai-masterclass).

> ▶️ **Run in VS Code — no Azure needed.** `pip install -r requirements.txt`, then `uvicorn app.main:app --reload` and open http://127.0.0.1:8000/docs. The SK kernel + plugin run **for real** offline; Azure OpenAI is optional.

---

## 🎯 What it shows
How to build an agent capability with [Semantic Kernel](https://learn.microsoft.com/semantic-kernel/):
a **Kernel** with a native **plugin** (`PolicyPlugin`) exposing a `@kernel_function`. The plugin runs for
real even without an LLM; when **Azure OpenAI** is configured, the kernel adds an `AzureChatCompletion`
service and uses **automatic function calling** so the model invokes the plugin itself.

## 🧩 How it works
- `PolicyPlugin.lookup_policy` — a native `@kernel_function` that validates a policy number.
- **Mock mode (default):** the service extracts the policy number and invokes the plugin via
  `kernel.invoke(plugin_name="policy", function_name="lookup_policy", ...)` — genuine SK execution.
- **Azure mode:** `kernel.invoke_prompt(..., FunctionChoiceBehavior.Auto())` lets the model decide to call
  the plugin; structured fields stay authoritative (re-derived from the plugin).

## 🚀 Quick start
```bash
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
```bash
curl -X POST http://127.0.0.1:8000/api/v1/claims/validate \
  -H "Content-Type: application/json" \
  -d '{"claim_text": "Minor accident, policy POL-12345, front bumper."}'
```
Run tests: `pytest -q`. Policies: `POL-12345`/`POL-67890` (active → approved), `POL-00001` (lapsed →
rejected), anything else (not found → needs_review).

## ☁️ Optional: Azure OpenAI (automatic function calling)
Set `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` (+ deployment) in `.env`. The kernel registers an
`AzureChatCompletion` service and the model auto-calls the plugin. `GET /health` reports `"mode": "azure"`.

> Dependency note: Semantic Kernel needs a newer `starlette` than FastAPI 0.115 allows, so this repo uses
> `fastapi>=0.136`. The Azure auto-function-calling import paths can vary across SK versions — verify
> against your installed `semantic-kernel` if you customize that path.

## 🏗️ How it maps to the course
This is the Semantic Kernel counterpart to
[Week 2 (Foundry claims intake)](https://github.com/satyajeetaiml-hue/agentic-ai-azure-week02-foundry-claims)
and the [Weeks 3–4 Agent Framework lab](https://github.com/satyajeetaiml-hue/agentic-ai-azure-week03-04-agent-framework)
— the same "tool/plugin the agent calls" idea, expressed in SK.

## 🧰 Tech stack
Semantic Kernel, Azure OpenAI (`AzureChatCompletion`), FastAPI, Pydantic v2.

## 📁 Structure
```
app/kernel_app.py  # Kernel, PolicyPlugin (kernel_function), validation logic
app/main.py        # FastAPI app + POST /api/v1/claims/validate
tests/test_app.py
```

## 📄 License
MIT — see [`LICENSE`](LICENSE).

## 📊 Teaching slides

Download the **7-slide deck** for classroom use: [`agentic-ai-azure-semantic-kernel.pptx`](slides/agentic-ai-azure-semantic-kernel.pptx)

> Slides: Title · Learning goal · Enterprise use case · Architecture/flow · Key concepts · Run it · Architect's takeaways.

