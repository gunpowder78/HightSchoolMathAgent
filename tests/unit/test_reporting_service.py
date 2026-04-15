from app.reporting.service import ReportingService


def test_reporting_service_builds_review_trend() -> None:
    service = ReportingService()
    review_runs = [
        {"review_score": 78, "pass_status": "pass", "trigger_repair": False},
        {"review_score": 74, "pass_status": "pass", "trigger_repair": False},
        {"review_score": 62, "pass_status": "fail", "trigger_repair": True},
        {"review_score": 58, "pass_status": "fail", "trigger_repair": True},
    ]

    trend = service.build_review_trend("student-report-01", review_runs)

    assert trend.sample_size == 4
    assert trend.latest_score == 78
    assert trend.pass_rate == 0.5
    assert trend.risk_trend == "improving"


def test_reporting_service_builds_parent_weekly_report() -> None:
    service = ReportingService()
    checkins = [
        {"completed": True, "note": "今天立体建系稳定"},
        {"completed": False, "note": ""},
        {"completed": True, "note": "三角函数错误减少"},
    ]

    report = service.build_parent_weekly_report("student-report-02", checkins, max_days=7)

    assert report["days"] == 3
    assert report["completion_rate"] == 0.6667
    assert len(report["highlights"]) == 2
    assert len(report["risks"]) >= 1


def test_reporting_service_exports_snapshot() -> None:
    service = ReportingService()
    snapshot = service.export_snapshot(
        student_id="student-report-03",
        latest_assessment={"student_id": "student-report-03"},
        latest_plan={"student_id": "student-report-03"},
        review_runs=[{"review_score": 60, "pass_status": "fail", "trigger_repair": True}],
        checkins=[{"completed": True, "note": "ok"}],
    )

    assert snapshot["student_id"] == "student-report-03"
    assert "review_trend" in snapshot
    assert "parent_weekly_report" in snapshot


def test_reporting_service_builds_alerts_and_chart_payload() -> None:
    service = ReportingService()
    trend = {
        "latest_score": 52.0,
        "pass_rate": 0.4,
        "repair_trigger_rate": 0.7,
        "risk_trend": "worsening",
    }
    weekly = {"completion_rate": 0.5}
    alerts = service.build_threshold_alerts(trend, weekly)
    assert len(alerts) >= 3

    custom_alerts = service.build_threshold_alerts(
        trend,
        weekly,
        thresholds={
            "latest_score_min": 50,
            "pass_rate_min": 0.3,
            "repair_rate_max": 0.9,
            "completion_rate_min": 0.4,
        },
    )
    assert custom_alerts == ["告警：趋势正在恶化，建议优先处理心理与掌控感恢复。"]

    chart_payload = service.build_chart_payload(
        review_runs=[{"review_score": 60, "trigger_repair": True}, {"review_score": 72, "trigger_repair": False}],
        checkins=[{"completed": True}, {"completed": False}],
    )
    html = service.build_simple_chart_html(chart_payload)
    assert "复评趋势" in html
    assert len(chart_payload["review_points"]) == 2


def test_reporting_service_can_render_markdown_snapshot() -> None:
    service = ReportingService()
    snapshot = {
        "student_id": "student-report-04",
        "review_trend": {
            "latest_score": 76,
            "average_score": 72,
            "pass_rate": 0.75,
            "repair_trigger_rate": 0.25,
            "risk_trend": "stable",
        },
        "parent_weekly_report": {
            "days": 7,
            "completion_rate": 0.86,
            "highlights": ["立体建系稳定"],
            "risks": ["执行节奏总体稳定"],
        },
        "review_samples": [],
        "checkin_samples": [],
    }
    md = service.to_markdown_snapshot(snapshot)
    assert md.startswith("# 学习快照")
    assert "student-report-04" in md


def test_reporting_service_builds_bulk_weekly_export() -> None:
    service = ReportingService()
    payload = service.build_bulk_weekly_export(
        [
            {"student_id": "s1", "weekly_report": {"completion_rate": 0.8, "risks": [], "days": 7}},
            {"student_id": "s2", "weekly_report": {"completion_rate": 0.4, "risks": ["x"], "days": 7}},
        ]
    )
    assert payload["student_count"] == 2
    assert payload["students"][1]["risk_count"] == 1
