"""Resolve config from ~/.config/exa/config.toml plus EXA_API_KEY env override."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "exa" / "config.toml"


@dataclass
class Config:
    api_key: str | None = None
    defaults: dict[str, Any] = field(default_factory=dict)
    source: str = "none"  # "env", "file", "file+env", "none"


def load() -> Config:
    cfg = Config()
    path = config_path()
    if path.exists():
        with path.open("rb") as f:
            data = tomllib.load(f)
        if isinstance(data.get("api_key"), str):
            cfg.api_key = data["api_key"]
            cfg.source = "file"
        d = data.get("defaults")
        if isinstance(d, dict):
            cfg.defaults = d

    env_key = os.environ.get("EXA_API_KEY")
    if env_key:
        cfg.api_key = env_key
        cfg.source = "file+env" if cfg.source == "file" else "env"

    return cfg


def redact(key: str | None) -> str:
    if not key:
        return "<unset>"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}…{key[-4:]}"
