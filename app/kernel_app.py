"""Semantic Kernel on Azure — Claims Validation with a native plugin.

A real **Semantic Kernel** ``Kernel`` with a native **plugin** (`PolicyPlugin`)
whose `@kernel_function` validates an insurance policy. The plugin runs **for real
offline** (no AI service needed). When Azure OpenAI is configured, the kernel adds
an `AzureChatCompletion` service and uses **automatic function calling** so the model
invokes the plugin itself.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelArguments, kernel_function


# ── settings ────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-10-21"

    @property
    def use_azure(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ── schemas ─────────────────────────────────────────────────────────────
class ClaimRequest(BaseModel):
    claim_text: str = Field(..., min_length=1, description="Free-text insurance claim.")


class ClaimValidation(BaseModel):
    policy_number: str | None
    valid: bool
    status: str
    coverage: list[str]
    decision: str  # approved | needs_review | rejected
    mode: str
    invoked_via: str
    summary: str | None = None


# ── the Semantic Kernel native plugin ───────────────────────────────────
_POLICIES = {
    "POL-12345": {"holder": "Jordan Avery", "status": "active",
                  "coverage": ["collision", "liability", "roadside"], "deductible": 500.0},
    "POL-67890": {"holder": "Sam Rivera", "status": "active",
                  "coverage": ["property", "contents", "flood"], "deductible": 1000.0},
    "POL-00001": {"holder": "Lapsed Customer", "status": "lapsed", "coverage": [], "deductible": None},
}


class PolicyPlugin:
    """A native SK plugin the kernel (or the model) can call."""

    @kernel_function(
        name="lookup_policy",
        description="Validate an insurance policy number; returns JSON with status, coverage, deductible.",
    )
    def lookup_policy(self, policy_number: str) -> str:
        rec = _POLICIES.get((policy_number or "").strip().upper())
        if rec is None:
            return json.dumps({"policy_number": policy_number, "valid": False, "status": "not_found",
                               "coverage": []})
        return json.dumps({
            "policy_number": policy_number,
            "valid": rec["status"] == "active",
            "status": rec["status"],
            "holder": rec["holder"],
            "coverage": rec["coverage"],
            "deductible": rec["deductible"],
        })


@lru_cache
def build_kernel() -> Kernel:
    """Build the kernel once: register the plugin (+ Azure chat service if configured)."""
    kernel = Kernel()
    kernel.add_plugin(PolicyPlugin(), plugin_name="policy")
    s = get_settings()
    if s.use_azure:
        from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

        kernel.add_service(
            AzureChatCompletion(
                deployment_name=s.azure_openai_deployment,
                endpoint=s.azure_openai_endpoint,
                api_key=s.azure_openai_api_key,
                api_version=s.azure_openai_api_version,
            )
        )
    return kernel


_POLICY_RE = re.compile(r"\bPOL-\d{4,6}\b", re.IGNORECASE)


def _extract_policy(text: str) -> str | None:
    m = _POLICY_RE.search(text)
    return m.group(0).upper() if m else None


def _decide(data: dict) -> str:
    status = data.get("status")
    if status in (None, "not_found", "missing"):
        return "needs_review"
    return "approved" if data.get("valid") else "rejected"


async def _plugin_validate(req: ClaimRequest) -> ClaimValidation:
    """Validate by invoking the SK native plugin via the kernel (real SK, no Azure)."""
    kernel = build_kernel()
    policy_number = _extract_policy(req.claim_text)
    result = await kernel.invoke(
        plugin_name="policy",
        function_name="lookup_policy",
        arguments=KernelArguments(policy_number=policy_number or ""),
    )
    data = json.loads(str(result))
    return ClaimValidation(
        policy_number=policy_number,
        valid=bool(data.get("valid")),
        status=data.get("status", "unknown"),
        coverage=data.get("coverage", []),
        decision=_decide(data),
        mode="mock",
        invoked_via="semantic-kernel native plugin",
    )


async def _azure_validate(req: ClaimRequest) -> ClaimValidation:
    """Let the Azure chat model call the plugin via automatic function calling.

    Structured fields stay authoritative (re-derived from the plugin); the model
    contributes a natural-language summary. Lazy-imported; runs only in azure mode.
    """
    from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
    from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings

    kernel = build_kernel()
    settings = AzureChatPromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto())
    summary = await kernel.invoke_prompt(
        f"Validate the policy in this claim and summarize the coverage:\n{req.claim_text}",
        arguments=KernelArguments(settings=settings),
    )

    base = await _plugin_validate(req)
    base.mode = "azure"
    base.invoked_via = "semantic-kernel + AzureChatCompletion (auto function calling)"
    base.summary = str(summary)
    return base


async def validate_claim(req: ClaimRequest) -> ClaimValidation:
    return await (_azure_validate(req) if get_settings().use_azure else _plugin_validate(req))
