from __future__ import annotations

from typing import Protocol

from app.domain.models import BugType, ProblemInput, SessionState


class TutorModelAdapter(Protocol):
    def classify_bug(self, problem: ProblemInput, state: SessionState) -> BugType:
        ...

    def render_guidance(
        self,
        problem: ProblemInput,
        state: SessionState,
        bug_type: BugType,
    ) -> tuple[str, str]:
        ...
