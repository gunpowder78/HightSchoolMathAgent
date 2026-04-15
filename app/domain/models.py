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
