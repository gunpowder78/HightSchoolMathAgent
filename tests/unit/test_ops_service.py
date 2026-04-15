from app.ops.service import OpsService


def test_ops_service_builds_dashboard_alerts() -> None:
    service = OpsService()
    payload = service.build_dashboard(
        metrics={
            "students_count": 2,
            "assessment_profiles_count": 1,
            "plan_versions_count": 1,
            "review_runs_count": 0,
            "repair_events_count": 0,
            "parent_checkins_count": 0,
        },
        gaps={"no_assessment": ["s2"], "no_plan": ["s2"], "no_review": ["s1", "s2"], "no_checkin": ["s1"]},
    )

    assert "metrics" in payload
    assert "gaps" in payload
    assert len(payload["alerts"]) >= 1
