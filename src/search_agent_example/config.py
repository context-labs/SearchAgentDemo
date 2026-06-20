from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    litellm_base_url: str
    litellm_api_key: str
    litellm_model_id: str
    tavily_api_key: str | None
    inference_net_api_key: str | None
    catalyst_endpoint: str
    catalyst_service_name: str
    max_tool_results: int = 5
    max_extract_chars: int = 6000


def load_settings(env_file: str | Path | None = ".env") -> Settings:
    if env_file:
        load_dotenv(env_file)

    inference_key = os.getenv("INFERENCE_NET_API_KEY")
    catalyst_token = os.getenv("CATALYST_OTLP_TOKEN") or inference_key
    if catalyst_token:
        os.environ.setdefault("CATALYST_OTLP_TOKEN", catalyst_token)

    os.environ.setdefault("CATALYST_OTLP_ENDPOINT", "https://telemetry.inference.net")
    os.environ.setdefault("CATALYST_SERVICE_NAME", "halo-search-agent-example")

    return Settings(
        litellm_base_url=require_env("LITELLM_BASE_URL"),
        litellm_api_key=require_env("LITELLM_API_KEY"),
        litellm_model_id=require_env("LITELLM_MODEL_ID"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        inference_net_api_key=inference_key,
        catalyst_endpoint=os.environ["CATALYST_OTLP_ENDPOINT"],
        catalyst_service_name=os.environ["CATALYST_SERVICE_NAME"],
    )


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
