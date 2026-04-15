from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    app_name: str = "HightSchoolMathAgent"
    database_path: Path = Path("data") / "hightschool_math_agent.db"
    prompt_root: Path = Path("prompts")
    use_fake_model: bool = True

    def ensure_runtime_dirs(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.prompt_root.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_runtime_dirs()
    return settings
