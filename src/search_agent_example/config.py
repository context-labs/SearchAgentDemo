from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_MODEL_ID = "gpt-4.1-mini"
DEFAULT_BASE_URL = "https://api.inference.net/v1"


@dataclass(frozen=True)
class Settings:
    inference_api_key: str
    inference_base_url: str
    model_id: str
    tavily_api_key: str | None
    catalyst_endpoint: str
    catalyst_service_name: str
    max_tool_results: int = 5
    max_extract_chars: int = 6000


def load_settings(env_file: str | Path | None = ".env") -> Settings:
    if env_file:
        load_dotenv(env_file)

    # A single INFERENCE_API_KEY powers both the model calls (through the
    # OpenAI-compatible endpoint at api.inference.net) and tracing (the tracing
    # SDK reads INFERENCE_API_KEY directly). Set the preferred INFERENCE_* tracing
    # vars; the SDK still honors the legacy CATALYST_* aliases if already set.
    inference_key = require_env("INFERENCE_API_KEY")
    os.environ.setdefault("INFERENCE_OTLP_ENDPOINT", "https://telemetry.inference.net")
    os.environ.setdefault("INFERENCE_SERVICE_NAME", "halo-search-agent-example")
    # Backfill the legacy aliases for older SDK versions that only read CATALYST_*.
    os.environ.setdefault("CATALYST_OTLP_TOKEN", inference_key)
    os.environ.setdefault("CATALYST_OTLP_ENDPOINT", os.environ["INFERENCE_OTLP_ENDPOINT"])
    os.environ.setdefault("CATALYST_SERVICE_NAME", os.environ["INFERENCE_SERVICE_NAME"])

    return Settings(
        inference_api_key=inference_key,
        inference_base_url=os.getenv("INFERENCE_BASE_URL", DEFAULT_BASE_URL),
        model_id=os.getenv("MODEL_ID", DEFAULT_MODEL_ID),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        catalyst_endpoint=os.environ["INFERENCE_OTLP_ENDPOINT"],
        catalyst_service_name=os.environ["INFERENCE_SERVICE_NAME"],
    )


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
