"""Thin wrapper around Ollama: structured JSON out, retries, and a clean failure mode.

Every AI step in the app goes through ask_json(). If Ollama is down or the model returns
something that doesn't match the schema, LLMUnavailable is raised and the caller falls
back to rule-based logic, so the app never crashes on a bad model response.
"""
import os

import ollama
from pydantic import BaseModel

# A bigger model follows JSON schemas much more reliably than a 3B one.
# e.g. AUTOREPORT_MODEL=llama3.1:8b  or  qwen2.5:7b
MODEL = os.getenv("AUTOREPORT_MODEL", "llama3.2")

_state = {"up": None}


class LLMUnavailable(Exception):
    pass


def check() -> bool:
    """Ping Ollama once and remember the answer until check() is called again."""
    try:
        ollama.list()
        _state["up"] = True
    except Exception:
        _state["up"] = False
    return _state["up"]


def ask_json(prompt: str, schema: type[BaseModel], system: str = "", retries: int = 1) -> BaseModel:
    """Ask the model for JSON that validates against `schema` (enforced by Ollama's structured outputs)."""
    if _state["up"] is False:
        raise LLMUnavailable("Ollama is not running")
    messages = ([{"role": "system", "content": system}] if system else [])
    messages.append({"role": "user", "content": prompt})
    error = None
    for _ in range(retries + 1):
        try:
            reply = ollama.chat(
                model=MODEL,
                messages=messages,
                format=schema.model_json_schema(),
                options={"temperature": 0.1},
            )
            return schema.model_validate_json(reply["message"]["content"])
        except Exception as e:  # connection errors, invalid JSON, schema mismatch
            error = e
    raise LLMUnavailable(str(error))