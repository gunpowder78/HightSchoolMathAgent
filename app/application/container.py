from __future__ import annotations

from dataclasses import dataclass

from app.assessment.service import AssessmentService
from app.config import Settings, get_settings
from app.model_adapters.fake_tutor import FakeTutorModelAdapter
from app.ops.service import OpsService
from app.parenting.service import ParentDashboardService
from app.planning.service import PlanningService
from app.persistence.sqlite_store import SQLiteStore
from app.repair.service import RepairService
from app.reporting.service import ReportingService
from app.review.service import ReviewService
from app.tutor_engine.service import TutorService


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    store: SQLiteStore
    tutor_service: TutorService
    assessment_service: AssessmentService
    planning_service: PlanningService
    review_service: ReviewService
    repair_service: RepairService
    parent_dashboard_service: ParentDashboardService
    reporting_service: ReportingService
    ops_service: OpsService


def build_container() -> AppContainer:
    settings = get_settings()
    store = SQLiteStore(settings.database_path)
    store.init_schema()
    tutor_service = TutorService(model_adapter=FakeTutorModelAdapter())
    assessment_service = AssessmentService()
    planning_service = PlanningService()
    review_service = ReviewService()
    repair_service = RepairService()
    parent_dashboard_service = ParentDashboardService()
    reporting_service = ReportingService()
    ops_service = OpsService()
    return AppContainer(
        settings=settings,
        store=store,
        tutor_service=tutor_service,
        assessment_service=assessment_service,
        planning_service=planning_service,
        review_service=review_service,
        repair_service=repair_service,
        parent_dashboard_service=parent_dashboard_service,
        reporting_service=reporting_service,
        ops_service=ops_service,
    )
