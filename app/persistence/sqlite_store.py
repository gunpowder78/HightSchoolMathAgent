from __future__ import annotations

import sqlite3
from pathlib import Path
import json


class SQLiteStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name_or_alias TEXT NOT NULL,
                    province TEXT NOT NULL,
                    exam_track TEXT NOT NULL,
                    target_score_range TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    current_goal TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'created',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS turns (
                    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS assessment_profiles (
                    assessment_profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    score_floor_estimate REAL NOT NULL,
                    defense_band TEXT NOT NULL,
                    cognitive_style_label TEXT NOT NULL,
                    psychological_risk_level TEXT NOT NULL,
                    module_mastery_json TEXT NOT NULL,
                    strategy_recommendation_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS plan_versions (
                    plan_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    planning_horizon_days INTEGER NOT NULL,
                    plan_json TEXT NOT NULL,
                    change_reason TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS review_runs (
                    review_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    target_node TEXT NOT NULL,
                    review_score REAL NOT NULL,
                    pass_status TEXT NOT NULL,
                    trigger_repair INTEGER NOT NULL,
                    suggested_action TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS repair_events (
                    repair_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    target_node TEXT NOT NULL,
                    protocol_id TEXT NOT NULL,
                    protocol_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS parent_checkins (
                    checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    day_index INTEGER NOT NULL,
                    completed INTEGER NOT NULL,
                    note TEXT NOT NULL,
                    dashboard_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS alert_thresholds (
                    student_id TEXT PRIMARY KEY,
                    latest_score_min REAL NOT NULL,
                    pass_rate_min REAL NOT NULL,
                    repair_rate_max REAL NOT NULL,
                    completion_rate_min REAL NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def upsert_student(
        self,
        student_id: str,
        name_or_alias: str,
        province: str = "广东",
        exam_track: str = "艺术生",
        target_score_range: str = "90-100",
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO students (student_id, name_or_alias, province, exam_track, target_score_range)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                  name_or_alias = excluded.name_or_alias,
                  province = excluded.province,
                  exam_track = excluded.exam_track,
                  target_score_range = excluded.target_score_range
                """,
                (student_id, name_or_alias, province, exam_track, target_score_range),
            )

    def create_session(self, student_id: str, current_goal: str) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO sessions (student_id, current_goal, status)
                VALUES (?, ?, 'created')
                """,
                (student_id, current_goal),
            )
            return int(cursor.lastrowid)

    def add_turn(self, session_id: int, role: str, content: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO turns (session_id, role, content)
                VALUES (?, ?, ?)
                """,
                (session_id, role, content),
            )

    def list_turns(self, session_id: int) -> list[dict[str, str]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content
                FROM turns
                WHERE session_id = ?
                ORDER BY turn_id ASC
                """,
                (session_id,),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    def save_assessment_profile(
        self,
        student_id: str,
        score_floor_estimate: float,
        defense_band: str,
        cognitive_style_label: str,
        psychological_risk_level: str,
        module_mastery: dict[str, str],
        strategy_recommendation: dict[str, object],
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO assessment_profiles (
                    student_id,
                    score_floor_estimate,
                    defense_band,
                    cognitive_style_label,
                    psychological_risk_level,
                    module_mastery_json,
                    strategy_recommendation_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    score_floor_estimate,
                    defense_band,
                    cognitive_style_label,
                    psychological_risk_level,
                    json.dumps(module_mastery, ensure_ascii=False),
                    json.dumps(strategy_recommendation, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def get_latest_assessment_profile(self, student_id: str) -> dict[str, object] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    assessment_profile_id,
                    student_id,
                    score_floor_estimate,
                    defense_band,
                    cognitive_style_label,
                    psychological_risk_level,
                    module_mastery_json,
                    strategy_recommendation_json,
                    created_at
                FROM assessment_profiles
                WHERE student_id = ?
                ORDER BY assessment_profile_id DESC
                LIMIT 1
                """,
                (student_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "assessment_profile_id": row["assessment_profile_id"],
            "student_id": row["student_id"],
            "score_floor_estimate": row["score_floor_estimate"],
            "defense_band": row["defense_band"],
            "cognitive_style_label": row["cognitive_style_label"],
            "psychological_risk_level": row["psychological_risk_level"],
            "module_mastery": json.loads(row["module_mastery_json"]),
            "strategy_recommendation": json.loads(row["strategy_recommendation_json"]),
            "created_at": row["created_at"],
        }

    def save_plan_version(
        self,
        student_id: str,
        planning_horizon_days: int,
        plan_json: dict[str, object],
        change_reason: str,
    ) -> int:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE plan_versions
                SET is_active = 0
                WHERE student_id = ?
                """,
                (student_id,),
            )
            cursor = conn.execute(
                """
                INSERT INTO plan_versions (
                    student_id,
                    planning_horizon_days,
                    plan_json,
                    change_reason,
                    is_active
                )
                VALUES (?, ?, ?, ?, 1)
                """,
                (student_id, planning_horizon_days, json.dumps(plan_json, ensure_ascii=False), change_reason),
            )
            return int(cursor.lastrowid)

    def get_latest_plan_version(self, student_id: str) -> dict[str, object] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    plan_version_id,
                    student_id,
                    planning_horizon_days,
                    plan_json,
                    change_reason,
                    is_active,
                    created_at
                FROM plan_versions
                WHERE student_id = ?
                ORDER BY plan_version_id DESC
                LIMIT 1
                """,
                (student_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "plan_version_id": row["plan_version_id"],
            "student_id": row["student_id"],
            "planning_horizon_days": row["planning_horizon_days"],
            "plan_json": json.loads(row["plan_json"]),
            "change_reason": row["change_reason"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
        }

    def get_latest_two_plan_versions(self, student_id: str) -> list[dict[str, object]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    plan_version_id,
                    student_id,
                    planning_horizon_days,
                    plan_json,
                    change_reason,
                    is_active,
                    created_at
                FROM plan_versions
                WHERE student_id = ?
                ORDER BY plan_version_id DESC
                LIMIT 2
                """,
                (student_id,),
            ).fetchall()
        result: list[dict[str, object]] = []
        for row in rows:
            result.append(
                {
                    "plan_version_id": row["plan_version_id"],
                    "student_id": row["student_id"],
                    "planning_horizon_days": row["planning_horizon_days"],
                    "plan_json": json.loads(row["plan_json"]),
                    "change_reason": row["change_reason"],
                    "is_active": bool(row["is_active"]),
                    "created_at": row["created_at"],
                }
            )
        return result

    def save_review_run(
        self,
        student_id: str,
        target_node: str,
        review_score: float,
        pass_status: str,
        trigger_repair: bool,
        suggested_action: str,
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO review_runs (
                    student_id,
                    target_node,
                    review_score,
                    pass_status,
                    trigger_repair,
                    suggested_action
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (student_id, target_node, review_score, pass_status, int(trigger_repair), suggested_action),
            )
            return int(cursor.lastrowid)

    def save_repair_event(
        self,
        student_id: str,
        target_node: str,
        protocol_id: str,
        protocol: dict[str, object],
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO repair_events (
                    student_id,
                    target_node,
                    protocol_id,
                    protocol_json
                )
                VALUES (?, ?, ?, ?)
                """,
                (student_id, target_node, protocol_id, json.dumps(protocol, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def save_parent_checkin(
        self,
        student_id: str,
        day_index: int,
        completed: bool,
        note: str,
        dashboard_payload: dict[str, object],
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO parent_checkins (
                    student_id,
                    day_index,
                    completed,
                    note,
                    dashboard_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_id, day_index, int(completed), note, json.dumps(dashboard_payload, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def list_recent_review_runs(self, student_id: str, limit: int = 20) -> list[dict[str, object]]:
        safe_limit = max(1, min(200, limit))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    review_run_id,
                    student_id,
                    target_node,
                    review_score,
                    pass_status,
                    trigger_repair,
                    suggested_action,
                    created_at
                FROM review_runs
                WHERE student_id = ?
                ORDER BY review_run_id DESC
                LIMIT ?
                """,
                (student_id, safe_limit),
            ).fetchall()
        result: list[dict[str, object]] = []
        for row in rows:
            result.append(
                {
                    "review_run_id": row["review_run_id"],
                    "student_id": row["student_id"],
                    "target_node": row["target_node"],
                    "review_score": row["review_score"],
                    "pass_status": row["pass_status"],
                    "trigger_repair": bool(row["trigger_repair"]),
                    "suggested_action": row["suggested_action"],
                    "created_at": row["created_at"],
                }
            )
        return result

    def list_parent_checkins(self, student_id: str, limit: int = 31) -> list[dict[str, object]]:
        safe_limit = max(1, min(365, limit))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    checkin_id,
                    student_id,
                    day_index,
                    completed,
                    note,
                    dashboard_json,
                    created_at
                FROM parent_checkins
                WHERE student_id = ?
                ORDER BY checkin_id DESC
                LIMIT ?
                """,
                (student_id, safe_limit),
            ).fetchall()
        result: list[dict[str, object]] = []
        for row in rows:
            result.append(
                {
                    "checkin_id": row["checkin_id"],
                    "student_id": row["student_id"],
                    "day_index": row["day_index"],
                    "completed": bool(row["completed"]),
                    "note": row["note"],
                    "dashboard": json.loads(row["dashboard_json"]),
                    "created_at": row["created_at"],
                }
            )
        return result

    def upsert_alert_thresholds(
        self,
        student_id: str,
        latest_score_min: float,
        pass_rate_min: float,
        repair_rate_max: float,
        completion_rate_min: float,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO alert_thresholds (
                    student_id,
                    latest_score_min,
                    pass_rate_min,
                    repair_rate_max,
                    completion_rate_min,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id) DO UPDATE SET
                  latest_score_min = excluded.latest_score_min,
                  pass_rate_min = excluded.pass_rate_min,
                  repair_rate_max = excluded.repair_rate_max,
                  completion_rate_min = excluded.completion_rate_min,
                  updated_at = CURRENT_TIMESTAMP
                """,
                (student_id, latest_score_min, pass_rate_min, repair_rate_max, completion_rate_min),
            )

    def get_alert_thresholds(self, student_id: str) -> dict[str, float] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    latest_score_min,
                    pass_rate_min,
                    repair_rate_max,
                    completion_rate_min
                FROM alert_thresholds
                WHERE student_id = ?
                LIMIT 1
                """,
                (student_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "latest_score_min": float(row["latest_score_min"]),
            "pass_rate_min": float(row["pass_rate_min"]),
            "repair_rate_max": float(row["repair_rate_max"]),
            "completion_rate_min": float(row["completion_rate_min"]),
        }

    def list_students(self) -> list[dict[str, str]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT student_id, name_or_alias
                FROM students
                ORDER BY student_id ASC
                """
            ).fetchall()
        return [{"student_id": row["student_id"], "name_or_alias": row["name_or_alias"]} for row in rows]

    def get_system_metrics(self) -> dict[str, int]:
        with self.connect() as conn:
            tables = [
                "students",
                "assessment_profiles",
                "plan_versions",
                "review_runs",
                "repair_events",
                "parent_checkins",
            ]
            metrics: dict[str, int] = {}
            for table in tables:
                row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
                metrics[f"{table}_count"] = int(row["c"]) if row else 0
        return metrics

    def get_data_quality_gaps(self) -> dict[str, list[str]]:
        students = [item["student_id"] for item in self.list_students()]
        no_assessment: list[str] = []
        no_plan: list[str] = []
        no_review: list[str] = []
        no_checkin: list[str] = []

        for sid in students:
            if self.get_latest_assessment_profile(sid) is None:
                no_assessment.append(sid)
            if self.get_latest_plan_version(sid) is None:
                no_plan.append(sid)
            if not self.list_recent_review_runs(sid, limit=1):
                no_review.append(sid)
            if not self.list_parent_checkins(sid, limit=1):
                no_checkin.append(sid)
        return {
            "no_assessment": no_assessment,
            "no_plan": no_plan,
            "no_review": no_review,
            "no_checkin": no_checkin,
        }
