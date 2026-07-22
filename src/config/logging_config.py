from __future__ import annotations

import logging
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "pipeline.log"


def setup_logging() -> None:
	LOGS_DIR.mkdir(parents=True, exist_ok=True)
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)-5s %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
		handlers=[
			logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
		],
		force=True,
	)