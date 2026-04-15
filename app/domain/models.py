from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


BugType = Literal["concept_confusion", "logic_step_skipping", "carelessness", "unknown"]


@dataclass(slots=True)
class ProblemInput:
    question_text: str
    student_attempt: str = ""
    student_question: str = ""
    image_path: str | None = None


@dataclass(slots=True)
class SessionState:
    known_conditions: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    rejected_paths: list[str] = field(default_factory=list)
    current_teaching_goal: str = "clarify_problem"
    scaffold_level: int = 0


@dataclass(slots=True)
class TutorResponse:
    information_sufficient: bool
    bug_type: BugType
    problem_summary: str
    teaching_goal: str
    guiding_question: str
    visual_hint: str
    teacher_note: str
    next_action: str


@dataclass(slots=True)
class StudentProfile:
    student_id: str
    name_or_alias: str
    province: str = "广东"
    exam_track: str = "艺术生"
    target_score_range: str = "90-100"


RiskLevel = Literal["low", "medium", "high"]
CognitiveStyle = Literal["visual_spatial_priority", "mixed_transition", "symbolic_tolerant"]


@dataclass(slots=True)
class AssessmentInput:
    student_id: str
    name_or_alias: str
    target_score_range: str
    daily_study_minutes: int
    latest_math_score: float
    single_choice_accuracy: float
    multi_choice_partial_accuracy: float
    fill_blank_accuracy: float
    basic_big_question_accuracy: float
    visual_preference_level: int
    symbolic_tolerance_level: int
    peer_pressure_level: int
    helplessness_level: int
    weak_modules: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AssessmentProfile:
    student_id: str
    score_floor_estimate: float
    defense_band: str
    cognitive_style_label: CognitiveStyle
    psychological_risk_level: RiskLevel
    module_mastery: dict[str, str]
    strategy_recommendation: dict[str, object]


@dataclass(slots=True)
class PlanningProfile:
    student_id: str
    planning_horizon_days: int
    primary_track: str
    weekly_objectives: list[str]
    daily_actions: list[dict[str, object]]
    guard_policy: dict[str, object]
    risk_action: str
