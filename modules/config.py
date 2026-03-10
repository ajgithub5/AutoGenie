from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from functools import lru_cache

import tomllib
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
default_config_path = project_root/"config.toml"

@dataclass
class Settings:
    # Default parameters and values
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    default_country: str = "US"
    default_annual_rate: float = 6.5
    default_loan_years: int = 5
    rag_docs_path: Path = project_root / "data" / "rag"
    car_catalog_path: Path = project_root / "data" / "cars" / "cars_catalog.json"
    vector_store_path: Path = project_root / "data" / "vectorstore"
    log_level: str = "INFO"

def load_config_toml(path: Path) -> dict[str, Any]:
    """
    Checks for config.toml file and opens it in read binary mode
    """
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)
    
@lru_cache(maxsize = 1)
def get_settings()->Settings:
    """
    Loads the seetings from environment variables and config.toml file.
    """
    load_dotenv()
    config_toml = load_config_toml(default_config_path).get("app", {})

    def _from_env_or_toml(key: str, default: Any) -> Any:
        env_val = os.getenv(key.upper())
        if env_val is not None:
            return env_val
        return config_toml.get(key, default)
    
    settings = Settings(
        openai_api_key = str(_from_env_or_toml("openai_api_key", "") or "") or None,
        openai_model=str(_from_env_or_toml("openai_model", Settings.openai_model)),
        openai_embedding_model=str(_from_env_or_toml("openai_embedding_model", Settings.openai_embedding_model)),
        default_country=str(_from_env_or_toml("default_country", Settings.default_country)),
        default_annual_rate=float(_from_env_or_toml("default_annual_rate", Settings.default_annual_rate)),
        default_loan_years=int(_from_env_or_toml("default_loan_years", Settings.default_loan_years)),
        rag_docs_path=Path(_from_env_or_toml("rag_docs_path", str(Settings.rag_docs_path))),
        car_catalog_path=Path(_from_env_or_toml("car_catalog_path", str(Settings.car_catalog_path))),
        vector_store_path=Path(_from_env_or_toml("vector_store_path", str(Settings.vector_store_path))),
        log_level=str(_from_env_or_toml("log_level", Settings.log_level)),
        )
    
    settings.rag_docs_path.mkdir(parents=True, exist_ok=True)
    settings.vector_store_path.mkdir(parents=True, exist_ok=True)

    return settings





