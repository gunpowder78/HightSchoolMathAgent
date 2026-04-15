from app.domain.models import AssessmentProfile, PlanningProfile
from app.parenting.service import ParentDashboardService
from app.repair.service import RepairService
from app.review.service import ReviewInput, ReviewService


def test_review_service_triggers_repair_for_low_scores() -> None:
    service = ReviewService()
    result = service.evaluate(
        ReviewInput(
            student_id="student-r-01",
            visual_reconstruction_score=40,
            mechanical_execution_score=42,
            feynman_explain_score=38,
            target_node="整体换元",
        )
    )
    assert result.pass_status == "fail"
    assert result.trigger_repair is True
    assert result.suggested_action == "触发熔断修复协议"


def test_repair_service_returns_specific_protocol() -> None:
    service = RepairService()
    protocol = service.get_protocol("立体建系")
    assert protocol["protocol_id"] == "RP-BUG-02"
    assert "实体模型" in "".join(protocol["steps"])


def test_parent_dashboard_service_builds_daily_view() -> None:
    service = ParentDashboardService()
    assessment = AssessmentProfile(
        student_id="student-p-01",
        score_floor_estimate=76.0,
        defense_band="foundation_rebuild",
        cognitive_style_label="mixed_transition",
        psychological_risk_level="high",
        module_mastery={"立体几何": "weak"},
        strategy_recommendation={},
    )
    plan = PlanningProfile(
        student_id="student-p-01",
        planning_horizon_days=7,
        primary_track="主线A先行+主线B并行",
        weekly_objectives=["稳固底盘"],
        daily_actions=[
            {
                "day": 1,
                "mode": "常规训练",
                "track_a_focus": "平面向量投影与数量积",
                "track_b_focus": "单位圆与弧度直观",
                "forbidden": ["压轴题深挖"],
                "track_a_minutes": 70,
                "track_b_minutes": 50,
            }
        ],
        guard_policy={},
        risk_action="启动掌控感修复",
    )

    dashboard = service.build_dashboard(assessment, plan, day_index=1)
    assert dashboard["risk_alert"] == "high"
    assert "平面向量投影与数量积" in dashboard["today_focus"][0]
    assert dashboard["execute_minutes"]["track_a"] == 70
