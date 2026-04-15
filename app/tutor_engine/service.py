from __future__ import annotations

from app.domain.models import ProblemInput, SessionState, TutorResponse
from app.model_adapters.base import TutorModelAdapter


class TutorService:
    def __init__(self, model_adapter: TutorModelAdapter) -> None:
        self.model_adapter = model_adapter

    def handle_problem(self, problem: ProblemInput, state: SessionState | None = None) -> TutorResponse:
        state = state or SessionState()
        normalized_question = problem.question_text.strip()

        if len(normalized_question) < 8:
            state.missing_information = ["题干过短，无法判断题型和已知条件"]
            return TutorResponse(
                information_sufficient=False,
                bug_type="unknown",
                problem_summary="当前题目信息不足，无法进入诊断阶段。",
                teaching_goal="clarify_problem",
                guiding_question="请补充完整题干，至少包含已知条件和你要求的目标。",
                visual_hint="如果方便，也可以补一张更清晰的题目截图。",
                teacher_note="先补足输入，再做错因归因。",
                next_action="clarify",
            )

        bug_type = self.model_adapter.classify_bug(problem, state)
        teacher_note, guiding_question = self.model_adapter.render_guidance(problem, state, bug_type)
        summary = f"已识别为本地 MVP 骨架流程，当前优先处理：{bug_type}。"

        visual_hint = self._pick_visual_hint(normalized_question)
        return TutorResponse(
            information_sufficient=True,
            bug_type=bug_type,
            problem_summary=summary,
            teaching_goal=self._pick_teaching_goal(bug_type),
            guiding_question=guiding_question,
            visual_hint=visual_hint,
            teacher_note=teacher_note,
            next_action="guide",
        )

    @staticmethod
    def _pick_teaching_goal(bug_type: str) -> str:
        mapping = {
            "concept_confusion": "rebuild_concept_anchor",
            "logic_step_skipping": "repair_reasoning_bridge",
            "carelessness": "recheck_local_calculation",
            "unknown": "clarify_problem",
        }
        return mapping.get(bug_type, "clarify_problem")

    @staticmethod
    def _pick_visual_hint(question_text: str) -> str:
        if any(keyword in question_text for keyword in ["向量", "数量积"]):
            return "先把题目想成“位移 + 投影”的画面，再决定公式。"
        if any(keyword in question_text for keyword in ["三角", "正弦", "余弦"]):
            return "先画单位圆或三角形草图，把角和边的位置钉住。"
        if any(keyword in question_text for keyword in ["立体", "几何", "二面角"]):
            return "先找“墙角”和垂线，再考虑坐标建系。"
        return "先把题目里的对象画出来，别急着做代数变形。"
