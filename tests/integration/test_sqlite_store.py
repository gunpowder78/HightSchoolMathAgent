from pathlib import Path

from app.persistence.sqlite_store import SQLiteStore


def test_sqlite_store_creates_session_and_turns(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()

    session_id = store.create_session("student-001", "clarify_problem")
    store.add_turn(session_id, "student", "题目是向量数量积")
    store.add_turn(session_id, "assistant", "先想投影")

    turns = store.list_turns(session_id)

    assert session_id > 0
    assert len(turns) == 2
    assert turns[0]["role"] == "student"
    assert turns[1]["content"] == "先想投影"


def test_sqlite_store_saves_and_reads_latest_assessment_profile(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()
    store.upsert_student("student-apt-01", "测试学生")

    store.save_assessment_profile(
        student_id="student-apt-01",
        score_floor_estimate=82.5,
        defense_band="rising_to_90",
        cognitive_style_label="visual_spatial_priority",
        psychological_risk_level="medium",
        module_mastery={"立体几何": "weak", "三角函数": "maintain"},
        strategy_recommendation={"primary_track": "主线A", "risk_action": "常规推进"},
    )
    latest = store.get_latest_assessment_profile("student-apt-01")

    assert latest is not None
    assert latest["student_id"] == "student-apt-01"
    assert latest["defense_band"] == "rising_to_90"
    assert latest["module_mastery"]["立体几何"] == "weak"


def test_sqlite_store_saves_and_reads_latest_plan_version(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()
    store.upsert_student("student-plan-01", "计划学生")

    store.save_plan_version(
        student_id="student-plan-01",
        planning_horizon_days=14,
        plan_json={
            "student_id": "student-plan-01",
            "primary_track": "主线A先行+主线B并行",
            "daily_actions": [{"day": 1, "mode": "常规训练"}],
        },
        change_reason="assessment_phase2_initial_plan",
    )
    latest = store.get_latest_plan_version("student-plan-01")

    assert latest is not None
    assert latest["student_id"] == "student-plan-01"
    assert latest["planning_horizon_days"] == 14
    assert latest["plan_json"]["primary_track"] == "主线A先行+主线B并行"
    assert latest["is_active"] is True


def test_sqlite_store_saves_review_and_repair_events(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()
    store.upsert_student("student-review-01", "复评学生")

    review_run_id = store.save_review_run(
        student_id="student-review-01",
        target_node="整体换元",
        review_score=54.0,
        pass_status="fail",
        trigger_repair=True,
        suggested_action="触发熔断修复协议",
    )
    repair_event_id = store.save_repair_event(
        student_id="student-review-01",
        target_node="整体换元",
        protocol_id="RP-BUG-01",
        protocol={"protocol_id": "RP-BUG-01", "name": "整体换元熔断修复"},
    )

    assert review_run_id > 0
    assert repair_event_id > 0


def test_sqlite_store_reads_latest_two_plan_versions_and_parent_checkin(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()
    store.upsert_student("student-plan-02", "计划学生2")

    store.save_plan_version(
        student_id="student-plan-02",
        planning_horizon_days=14,
        plan_json={"student_id": "student-plan-02", "primary_track": "主线A"},
        change_reason="v1",
    )
    store.save_plan_version(
        student_id="student-plan-02",
        planning_horizon_days=14,
        plan_json={"student_id": "student-plan-02", "primary_track": "主线A先行+主线B并行"},
        change_reason="v2",
    )
    versions = store.get_latest_two_plan_versions("student-plan-02")

    checkin_id = store.save_parent_checkin(
        student_id="student-plan-02",
        day_index=3,
        completed=True,
        note="今日完成良好",
        dashboard_payload={"student_id": "student-plan-02", "day": 3},
    )

    assert len(versions) == 2
    assert versions[0]["change_reason"] == "v2"
    assert versions[1]["change_reason"] == "v1"
    assert checkin_id > 0


def test_sqlite_store_lists_recent_review_runs_and_checkins(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()
    store.upsert_student("student-report-01", "报告学生")

    store.save_review_run(
        student_id="student-report-01",
        target_node="整体换元",
        review_score=66,
        pass_status="fail",
        trigger_repair=True,
        suggested_action="触发熔断修复协议",
    )
    store.save_review_run(
        student_id="student-report-01",
        target_node="立体建系",
        review_score=78,
        pass_status="pass",
        trigger_repair=False,
        suggested_action="继续当前计划",
    )
    store.save_parent_checkin(
        student_id="student-report-01",
        day_index=1,
        completed=True,
        note="已完成今日训练",
        dashboard_payload={"student_id": "student-report-01", "day": 1},
    )

    reviews = store.list_recent_review_runs("student-report-01", limit=10)
    checkins = store.list_parent_checkins("student-report-01", limit=10)

    assert len(reviews) == 2
    assert reviews[0]["target_node"] == "立体建系"
    assert len(checkins) == 1
    assert checkins[0]["completed"] is True


def test_sqlite_store_thresholds_and_ops_queries(tmp_path: Path) -> None:
    database_path = tmp_path / "agent.db"
    store = SQLiteStore(database_path)
    store.init_schema()
    store.upsert_student("student-ops-01", "运维学生")

    store.upsert_alert_thresholds(
        student_id="student-ops-01",
        latest_score_min=62,
        pass_rate_min=0.55,
        repair_rate_max=0.45,
        completion_rate_min=0.65,
    )
    thresholds = store.get_alert_thresholds("student-ops-01")
    students = store.list_students()
    metrics = store.get_system_metrics()
    gaps = store.get_data_quality_gaps()

    assert thresholds is not None
    assert thresholds["latest_score_min"] == 62
    assert any(s["student_id"] == "student-ops-01" for s in students)
    assert metrics["students_count"] >= 1
    assert "no_plan" in gaps
