from __future__ import annotations

from app.domain.models import BugType, ProblemInput, SessionState


class FakeTutorModelAdapter:
    """Deterministic fallback adapter for local MVP skeleton."""

    def classify_bug(self, problem: ProblemInput, state: SessionState) -> BugType:
        text = " ".join(
            [problem.question_text.lower(), problem.student_attempt.lower(), problem.student_question.lower()]
        )
        if any(keyword in text for keyword in ["概念", "定义", "为什么", "不懂", "不会"]):
            return "concept_confusion"
        if any(keyword in text for keyword in ["算错", "粗心", "正负号", "加减", "乘除"]):
            return "carelessness"
        if problem.student_attempt.strip():
            return "logic_step_skipping"
        return "unknown"

    def render_guidance(
        self,
        problem: ProblemInput,
        state: SessionState,
        bug_type: BugType,
    ) -> tuple[str, str]:
        if bug_type == "concept_confusion":
            return (
                "你先别急着套公式，我们先把题目里的核心概念翻成一句人话。",
                "如果把这道题画成图，哪个量最像“位置、影子、旋转”中的一种？",
            )
        if bug_type == "carelessness":
            return (
                "这题更像是计算链出了小偏差，不一定是思路错了。",
                "你回头只检查从上一步到下一步的符号变化，先别重做整题。",
            )
        if bug_type == "logic_step_skipping":
            return (
                "你的方向大概率是对的，但中间缺了一座桥。",
                "你从当前这一步推到下一步，依赖的是哪条公式或哪个定理？",
            )
        return (
            "现在信息还不够，我先帮你把问题钉住。",
            "请补一句：你卡住的是读题、建模、公式选择，还是最后计算？",
        )
