from __future__ import annotations

from app.domain.models import AssessmentProfile, PlanningProfile


class ParentDashboardService:
    """Build concise parent execution dashboard for daily coaching."""

    def build_dashboard(
        self,
        assessment_profile: AssessmentProfile,
        planning_profile: PlanningProfile,
        day_index: int,
    ) -> dict[str, object]:
        day_index = max(1, min(len(planning_profile.daily_actions), day_index))
        day_action = planning_profile.daily_actions[day_index - 1]

        encouragement = "今天以稳定为主，完成白名单动作就算赢。"
        if assessment_profile.psychological_risk_level == "high":
            encouragement = "先保掌控感，允许慢一点，但每一步都要做对。"

        return {
            "student_id": assessment_profile.student_id,
            "day": day_index,
            "today_focus": [
                day_action.get("track_a_focus", ""),
                day_action.get("track_b_focus", ""),
            ],
            "today_mode": day_action.get("mode", "常规训练"),
            "forbidden_items": day_action.get("forbidden", []),
            "encouragement": encouragement,
            "risk_alert": assessment_profile.psychological_risk_level,
            "execute_minutes": {
                "track_a": day_action.get("track_a_minutes", 0),
                "track_b": day_action.get("track_b_minutes", 0),
            },
        }
