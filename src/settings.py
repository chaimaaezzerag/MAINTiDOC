"""Configuration locale, budgets stricts et chemins du projet."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".local"
DATA = ROOT / "data/processed"
MODEL = "qwen2.5vl:3b"
MAX_SECONDS = 60
MAX_MODEL_CALLS = 6
MAX_MCP_CALLS = 3
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_CONTEXT = 14000
