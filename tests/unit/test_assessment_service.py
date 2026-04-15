from app.assessment.service import AssessmentService
from app.domain.models import AssessmentInput


def test_assessment_service_estimates_floor_and_visual_style() -> None:
    service = AssessmentService()
    assessment_input = AssessmentInput(
        student_id="student-apt-01",
        name_or_alias="测试学生",
        target_score_range="90-100",
        daily_study_minutes=120,
        latest_math_score=63,
        single_choice_accuracy=70,
        multi_choice_partial_accuracy=50,
        fill_blank_accuracy=40,
        basic_big_question_accuracy=45,
        visual_preference_level=5,
        symbolic_tolerance_level=2,
        peer_pressure_level=4,
        helplessness_level=3,
        weak_modules=["立体几何", "三角函数"],
    )

    profile = service.run_assessment(assessment_input)

    assert profile.score_floor_estimate > 60
    assert profile.cognitive_style_label == "visual_spatial_priority"
    assert profile.module_mastery["立体几何"] == "weak"
    assert profile.strategy_recommendation["primary_track"] == "主线A"


def test_assessment_service_sets_high_risk_with_low_time_and_high_pressure() -> None:
    service = AssessmentService()
    assessment_input = AssessmentInput(
        student_id="student-apt-02",
        name_or_alias="高压学生",
        target_score_range="90-100",
        daily_study_minutes=60,
        latest_math_score=48,
        single_choice_accuracy=50,
        multi_choice_partial_accuracy=30,
        fill_blank_accuracy=25,
        basic_big_question_accuracy=20,
        visual_preference_level=3,
        symbolic_tolerance_level=2,
        peer_pressure_level=5,
        helplessness_level=5,
        weak_modules=["平面向量", "立体几何", "解析几何基础问"],
    )

    profile = service.run_assessment(assessment_input)

    assert profile.psychological_risk_level == "high"
    assert profile.defense_band == "foundation_rebuild"
    assert profile.strategy_recommendation["risk_action"] == "启动掌控感修复"
