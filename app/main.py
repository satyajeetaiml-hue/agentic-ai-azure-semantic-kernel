"""Semantic Kernel on Azure — Claims Validation (FastAPI service).

Uses a real SK kernel + native plugin. Works offline (mock mode); set Azure OpenAI
env vars for automatic function calling. Run:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.kernel_app import ClaimRequest, ClaimValidation, get_settings, validate_claim

settings = get_settings()
app = FastAPI(title="Semantic Kernel — Claims Validation", version="0.1.0")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "framework": "semantic-kernel",
        "mode": "azure" if settings.use_azure else "mock",
    }


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "service": "agentic-ai-azure-semantic-kernel",
        "endpoint": "/api/v1/claims/validate",
        "mode": "azure" if settings.use_azure else "mock",
        "docs": "/docs",
    }


@app.post("/api/v1/claims/validate", response_model=ClaimValidation, tags=["semantic-kernel"])
async def validate(payload: ClaimRequest) -> ClaimValidation:
    return await validate_claim(payload)
