from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class ReviewInput:
    student_id: str
    visual_reconstruction_score: float
    mechanical_execution_score: float
    feynman_explain_score: float
    target_node: str


@dataclass(slots=True)
class ReviewResult:
    student_id: str
    review_score: float
    pass_status: str
    trigger_repair: bool
    target_node: str
    suggested_action: str


class ReviewService:
    """Three-slice micro review evaluator."""

    def evaluate(self, review_input: ReviewInput) -> ReviewResult:
        visual = _clamp_score(review_input.visual_reconstruction_score)
        mechanical = _clamp_score(review_input.mechanical_execution_score)
        feynman = _clamp_score(review_input.feynman_explain_score)
        review_score = visual * 0.3 + mechanical * 0.4 + feynman * 0.3

        pass_status = "pass" if review_score >= 70 else "fail"
        trigger_repair = review_score < 60 or min(visual, mechanical, feynman) < 45
        suggested_action = "继续当前计划"
        if pass_status == "fail":
            suggested_action = "降速并补做同层级基础题"
        if trigger_repair:
            suggested_action = "触发熔断修复协议"

        return ReviewResult(
            student_id=review_input.student_id,
            review_score=round(review_score, 2),
            pass_status=pass_status,
            trigger_repair=trigger_repair,
            target_node=review_input.target_node,
            suggested_action=suggested_action,
        )

    @staticmethod
    def serialize(result: ReviewResult) -> dict[str, object]:
        return asdict(result)


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))
