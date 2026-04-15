from app.domain.models import AssessmentProfile
from app.planning.service import PlanningService


def test_planning_service_generates_dual_track_actions() -> None:
    service = PlanningService()
    profile = AssessmentProfile(
        student_id="student-plan-01",
        score_floor_estimate=84.0,
        defense_band="rising_to_90",
        cognitive_style_label="visual_spatial_priority",
        psychological_risk_level="medium",
        module_mastery={"立体几何": "weak", "三角函数": "maintain"},
        strategy_recommendation={
            "primary_track": "主线A先行+主线B并行",
            "risk_action": "常规推进",
            "guard_policy": {"multi_choice_policy": "保守残缺得分"},
        },
    )

    plan = service.generate_plan(profile=profile, planning_horizon_days=14, daily_study_minutes=120)

    assert plan.primary_track == "主线A先行+主线B并行"
    assert len(plan.daily_actions) == 14
    assert plan.daily_actions[0]["track_a_minutes"] > plan.daily_actions[0]["track_b_minutes"]
    assert "稳固防御底盘" in plan.weekly_objectives[0]


def test_planning_service_has_review_every_third_day() -> None:
    service = PlanningService()
    profile = AssessmentProfile(
        student_id="student-plan-02",
        score_floor_estimate=58.0,
        defense_band="foundation_rebuild",
        cognitive_style_label="mixed_transition",
        psychological_risk_level="high",
        module_mastery={"平面向量": "weak", "导数基础问": "weak"},
        strategy_recommendation={
            "primary_track": "主线A先行+主线B并行",
            "risk_action": "启动掌控感修复",
            "guard_policy": {},
        },
    )

    plan = service.generate_plan(profile=profile, planning_horizon_days=9, daily_study_minutes=90)

    assert plan.daily_actions[2]["mode"] == "三题切片复评"
    assert plan.daily_actions[5]["mode"] == "三题切片复评"
    assert plan.risk_action == "启动掌控感修复"


def test_planning_service_replans_after_failed_review() -> None:
    service = PlanningService()
    profile = AssessmentProfile(
        student_id="student-plan-03",
        score_floor_estimate=70.0,
        defense_band="rising_to_90",
        cognitive_style_label="mixed_transition",
        psychological_risk_level="medium",
        module_mastery={"整体换元": "weak"},
        strategy_recommendation={
            "primary_track": "主线A先行+主线B并行",
            "risk_action": "常规推进",
            "guard_policy": {},
        },
    )
    old_plan = service.generate_plan(profile=profile, planning_horizon_days=14, daily_study_minutes=120)
    new_plan = service.replan_after_review(
        profile=profile,
        current_plan=old_plan,
        review_payload={"pass_status": "fail", "trigger_repair": True, "target_node": "整体换元"},
        daily_study_minutes=120,
    )
    diff = service.diff_plan_payloads(service.serialize_plan(old_plan), service.serialize_plan(new_plan))

    assert new_plan.weekly_objectives[0].startswith("熔断修复优先")
    assert any(item["mode_to"] == "修复优先训练" for item in diff["daily_action_changes"])
    assert len(diff["weekly_objectives_added"]) >= 1
