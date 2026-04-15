from __future__ import annotations


class OpsService:
    """Simple operations dashboard and data quality inspector."""

    def build_dashboard(self, metrics: dict[str, int], gaps: dict[str, list[str]]) -> dict[str, object]:
        alerts: list[str] = []
        if metrics.get("students_count", 0) == 0:
            alerts.append("系统暂无学生数据，建议先完成学情建档。")
        if metrics.get("assessment_profiles_count", 0) < metrics.get("students_count", 0):
            alerts.append("部分学生尚未生成学情画像。")
        if metrics.get("plan_versions_count", 0) < metrics.get("students_count", 0):
            alerts.append("部分学生尚未生成计划版本。")
        if gaps.get("no_checkin"):
            alerts.append("存在未打卡学生，家长执行链路可能中断。")
        if not alerts:
            alerts.append("系统运行状态正常。")

        return {
            "metrics": metrics,
            "gaps": gaps,
            "alerts": alerts,
        }
