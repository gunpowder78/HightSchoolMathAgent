from app.domain.models import ProblemInput, SessionState
from app.model_adapters.fake_tutor import FakeTutorModelAdapter
from app.tutor_engine.service import TutorService


def test_handle_problem_requires_more_information_when_question_is_too_short() -> None:
    service = TutorService(FakeTutorModelAdapter())

    response = service.handle_problem(ProblemInput(question_text="太短"), SessionState())

    assert response.information_sufficient is False
    assert response.next_action == "clarify"
    assert "补充完整题干" in response.guiding_question


def test_handle_problem_marks_concept_confusion_for_definition_question() -> None:
    service = TutorService(FakeTutorModelAdapter())
    problem = ProblemInput(
        question_text="已知三角函数题，求化简结果",
        student_attempt="我不会判断为什么这里能用诱导公式",
        student_question="这个定义我不懂",
    )

    response = service.handle_problem(problem, SessionState())

    assert response.information_sufficient is True
    assert response.bug_type == "concept_confusion"
    assert response.teaching_goal == "rebuild_concept_anchor"
