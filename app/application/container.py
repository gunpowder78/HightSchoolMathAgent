from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings, get_settings
from app.model_adapters.fake_tutor import FakeTutorModelAdapter
from app.persistence.sqlite_store import SQLiteStore
from app.tutor_engine.service import TutorService


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    store: SQLiteStore
    tutor_service: TutorService


def build_container() -> AppContainer:
    settings = get_settings()
    store = SQLiteStore(settings.database_path)
    store.init_schema()
    tutor_service = TutorService(model_adapter=FakeTutorModelAdapter())
    return AppContainer(settings=settings, store=store, tutor_service=tutor_service)
