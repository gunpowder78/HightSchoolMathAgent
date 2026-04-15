from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class ReviewTrend:
    student_id: str
    sample_size: int
    average_score: float
    latest_score: float
    pass_rate: float
    repair_trigger_rate: float
    risk_trend: str


class ReportingService:
    """Batch-5 reporting services: trend, weekly aggregation and snapshot export."""

    def build_review_trend(self, student_id: str, review_runs: list[dict[str, object]]) -> ReviewTrend:
        if not review_runs:
            return ReviewTrend(
                student_id=student_id,
                sample_size=0,
                average_score=0.0,
                latest_score=0.0,
                pass_rate=0.0,
                repair_trigger_rate=0.0,
                risk_trend="insufficient_data",
            )

        scores = [float(item.get("review_score", 0.0)) for item in review_runs]
        pass_count = sum(1 for item in review_runs if item.get("pass_status") == "pass")
        repair_count = sum(1 for item in review_runs if bool(item.get("trigger_repair", False)))
        latest_score = scores[0]

        trend = "stable"
        if len(scores) >= 4:
            recent = sum(scores[:2]) / 2
            older = sum(scores[-2:]) / 2
            if recent - older >= 8:
                trend = "improving"
            elif older - recent >= 8:
                trend = "worsening"

        return ReviewTrend(
            student_id=student_id,
            sample_size=len(scores),
            average_score=round(sum(scores) / len(scores), 2),
            latest_score=round(latest_score, 2),
            pass_rate=round(pass_count / len(scores), 4),
            repair_trigger_rate=round(repair_count / len(scores), 4),
            risk_trend=trend,
        )

    def build_parent_weekly_report(
        self,
        student_id: str,
        checkins: list[dict[str, object]],
        max_days: int = 7,
    ) -> dict[str, object]:
        recent = checkins[: max(1, max_days)]
        if not recent:
            return {
                "student_id": student_id,
                "days": 0,
                "completion_rate": 0.0,
                "highlights": [],
                "risks": ["暂无打卡数据"],
            }

        completed_count = sum(1 for item in recent if item.get("completed", False))
        notes = [str(item.get("note", "")).strip() for item in recent if str(item.get("note", "")).strip()]
        risks: list[str] = []
        if completed_count / len(recent) < 0.6:
            risks.append("执行完成率偏低，建议降低单日负荷并强化家长协同")
        if not notes:
            risks.append("缺少过程备注，建议记录卡点以支持下周调参")

        return {
            "student_id": student_id,
            "days": len(recent),
            "completion_rate": round(completed_count / len(recent), 4),
            "highlights": notes[:3] if notes else ["暂无文字亮点，建议补充记录"],
            "risks": risks if risks else ["执行节奏总体稳定"],
        }

    def export_snapshot(
        self,
        student_id: str,
        latest_assessment: dict[str, object] | None,
        latest_plan: dict[str, object] | None,
        review_runs: list[dict[str, object]],
        checkins: list[dict[str, object]],
    ) -> dict[str, object]:
        trend = self.build_review_trend(student_id, review_runs)
        weekly = self.build_parent_weekly_report(student_id, checkins, max_days=7)
        return {
            "student_id": student_id,
            "latest_assessment": latest_assessment or {},
            "latest_plan": latest_plan or {},
            "review_trend": asdict(trend),
            "parent_weekly_report": weekly,
            "review_samples": review_runs[:10],
            "checkin_samples": checkins[:10],
        }

    def build_threshold_alerts(
        self,
        trend_payload: dict[str, object],
        weekly_payload: dict[str, object],
        thresholds: dict[str, float] | None = None,
    ) -> list[str]:
        cfg = thresholds or {}
        latest_score_min = float(cfg.get("latest_score_min", 60.0))
        pass_rate_min = float(cfg.get("pass_rate_min", 0.5))
        repair_rate_max = float(cfg.get("repair_rate_max", 0.5))
        completion_rate_min = float(cfg.get("completion_rate_min", 0.6))

        alerts: list[str] = []
        latest_score = float(trend_payload.get("latest_score", 0.0))
        pass_rate = float(trend_payload.get("pass_rate", 0.0))
        repair_rate = float(trend_payload.get("repair_trigger_rate", 0.0))
        risk_trend = str(trend_payload.get("risk_trend", "stable"))
        completion_rate = float(weekly_payload.get("completion_rate", 0.0))

        if latest_score < latest_score_min:
            alerts.append(f"告警：最新复评分数低于 {latest_score_min:.0f}，建议立即降速并执行熔断修复。")
        if pass_rate < pass_rate_min:
            alerts.append(f"告警：复评通过率低于 {int(pass_rate_min * 100)}%，建议收缩训练范围到白名单基础题。")
        if repair_rate > repair_rate_max:
            alerts.append("告警：修复触发率偏高，说明当前计划负荷过大。")
        if completion_rate < completion_rate_min:
            alerts.append("告警：家长执行完成率低于 60%，建议降低单日任务并增加复盘。")
        if risk_trend == "worsening":
            alerts.append("告警：趋势正在恶化，建议优先处理心理与掌控感恢复。")
        if not alerts:
            alerts.append("状态良好：暂无关键阈值告警。")
        return alerts

    def build_chart_payload(
        self,
        review_runs: list[dict[str, object]],
        checkins: list[dict[str, object]],
    ) -> dict[str, object]:
        review_points: list[dict[str, object]] = []
        # reverse to old->new for plotting
        for idx, item in enumerate(reversed(review_runs), start=1):
            review_points.append(
                {
                    "index": idx,
                    "score": float(item.get("review_score", 0.0)),
                    "trigger_repair": bool(item.get("trigger_repair", False)),
                }
            )

        completion_points: list[dict[str, object]] = []
        for idx, item in enumerate(reversed(checkins), start=1):
            completion_points.append(
                {
                    "index": idx,
                    "completed": 100 if bool(item.get("completed", False)) else 0,
                }
            )
        return {"review_points": review_points, "completion_points": completion_points}

    def build_simple_chart_html(self, chart_payload: dict[str, object]) -> str:
        review_points = list(chart_payload.get("review_points", []))
        completion_points = list(chart_payload.get("completion_points", []))
        review_rows = "".join(
            f"<tr><td>{p['index']}</td><td>{p['score']}</td><td>{'是' if p['trigger_repair'] else '否'}</td></tr>"
            for p in review_points
        )
        completion_rows = "".join(
            f"<tr><td>{p['index']}</td><td>{p['completed']}%</td></tr>" for p in completion_points
        )
        if not review_rows:
            review_rows = "<tr><td colspan='3'>暂无复评数据</td></tr>"
        if not completion_rows:
            completion_rows = "<tr><td colspan='2'>暂无打卡数据</td></tr>"
        return (
            "<div style='display:flex;gap:16px;flex-wrap:wrap'>"
            "<div style='min-width:320px'><h4>复评趋势</h4>"
            "<table border='1' cellpadding='6' cellspacing='0'><tr><th>序号</th><th>分数</th><th>触发修复</th></tr>"
            f"{review_rows}</table></div>"
            "<div style='min-width:260px'><h4>执行完成率</h4>"
            "<table border='1' cellpadding='6' cellspacing='0'><tr><th>序号</th><th>完成率</th></tr>"
            f"{completion_rows}</table></div>"
            "</div>"
        )

    def to_markdown_snapshot(self, snapshot: dict[str, object]) -> str:
        trend = snapshot.get("review_trend", {})
        weekly = snapshot.get("parent_weekly_report", {})
        lines = [
            "# 学习快照",
            "",
            f"- 学生ID：{snapshot.get('student_id', '')}",
            f"- 复评样本数：{len(snapshot.get('review_samples', []))}",
            f"- 打卡样本数：{len(snapshot.get('checkin_samples', []))}",
            "",
            "## 复评趋势",
            f"- 最新分：{trend.get('latest_score', 0)}",
            f"- 平均分：{trend.get('average_score', 0)}",
            f"- 通过率：{trend.get('pass_rate', 0)}",
            f"- 修复触发率：{trend.get('repair_trigger_rate', 0)}",
            f"- 趋势：{trend.get('risk_trend', 'insufficient_data')}",
            "",
            "## 家长周报",
            f"- 统计天数：{weekly.get('days', 0)}",
            f"- 完成率：{weekly.get('completion_rate', 0)}",
            f"- 亮点：{'; '.join(weekly.get('highlights', []))}",
            f"- 风险：{'; '.join(weekly.get('risks', []))}",
        ]
        return "\n".join(lines)

    def build_bulk_weekly_export(
        self,
        student_payloads: list[dict[str, object]],
    ) -> dict[str, object]:
        summaries: list[dict[str, object]] = []
        for payload in student_payloads:
            sid = str(payload.get("student_id", ""))
            weekly = dict(payload.get("weekly_report", {}))
            summaries.append(
                {
                    "student_id": sid,
                    "completion_rate": weekly.get("completion_rate", 0.0),
                    "risk_count": len(weekly.get("risks", [])),
                    "days": weekly.get("days", 0),
                }
            )
        return {
            "student_count": len(summaries),
            "students": summaries,
        }

    @staticmethod
    def serialize_trend(trend: ReviewTrend) -> dict[str, object]:
        return asdict(trend)
