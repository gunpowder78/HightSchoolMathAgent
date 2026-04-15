from __future__ import annotations

from dataclasses import asdict

from app.domain.models import AssessmentProfile, PlanningProfile


class PlanningService:
    """MVP phase-2: dynamic defense planning with dual-track schedule."""

    def generate_plan(
        self,
        profile: AssessmentProfile,
        planning_horizon_days: int,
        daily_study_minutes: int,
    ) -> PlanningProfile:
        planning_horizon_days = max(7, min(28, planning_horizon_days))
        daily_study_minutes = max(45, min(300, daily_study_minutes))

        primary_track = self._resolve_primary_track(profile)
        weekly_objectives = self._build_weekly_objectives(profile, primary_track)
        daily_actions = self._build_daily_actions(
            profile=profile,
            primary_track=primary_track,
            planning_horizon_days=planning_horizon_days,
            daily_study_minutes=daily_study_minutes,
        )
        return PlanningProfile(
            student_id=profile.student_id,
            planning_horizon_days=planning_horizon_days,
            primary_track=primary_track,
            weekly_objectives=weekly_objectives,
            daily_actions=daily_actions,
            guard_policy=profile.strategy_recommendation.get("guard_policy", {}),
            risk_action=str(profile.strategy_recommendation.get("risk_action", "常规推进")),
        )

    def replan_after_review(
        self,
        profile: AssessmentProfile,
        current_plan: PlanningProfile,
        review_payload: dict[str, object],
        daily_study_minutes: int,
    ) -> PlanningProfile:
        trigger_repair = bool(review_payload.get("trigger_repair", False))
        pass_status = str(review_payload.get("pass_status", "pass"))
        planning_horizon_days = current_plan.planning_horizon_days

        # Default policy: fail -> slow down and increase review frequency.
        adjusted_minutes = max(45, int(daily_study_minutes * 0.9)) if pass_status == "fail" else daily_study_minutes
        new_plan = self.generate_plan(
            profile=profile,
            planning_horizon_days=planning_horizon_days,
            daily_study_minutes=adjusted_minutes,
        )

        if pass_status == "fail":
            new_plan.weekly_objectives.insert(0, "复评失败后降速：先稳住白名单基础动作")
        if trigger_repair:
            target_node = str(review_payload.get("target_node", "通用节点"))
            new_plan.weekly_objectives.insert(0, f"熔断修复优先：{target_node}")
            for action in new_plan.daily_actions:
                if action["day"] % 2 == 0:
                    action["mode"] = "修复优先训练"
        return new_plan

    @staticmethod
    def serialize_plan(plan: PlanningProfile) -> dict[str, object]:
        return asdict(plan)

    def diff_plan_payloads(self, old_plan: dict[str, object], new_plan: dict[str, object]) -> dict[str, object]:
        old_obj = set(old_plan.get("weekly_objectives", []))
        new_obj = set(new_plan.get("weekly_objectives", []))
        old_actions = old_plan.get("daily_actions", [])
        new_actions = new_plan.get("daily_actions", [])
        minute_deltas: list[dict[str, object]] = []
        for old_item, new_item in zip(old_actions, new_actions):
            if old_item.get("track_a_minutes") != new_item.get("track_a_minutes") or old_item.get("mode") != new_item.get("mode"):
                minute_deltas.append(
                    {
                        "day": new_item.get("day"),
                        "track_a_minutes_from": old_item.get("track_a_minutes"),
                        "track_a_minutes_to": new_item.get("track_a_minutes"),
                        "mode_from": old_item.get("mode"),
                        "mode_to": new_item.get("mode"),
                    }
                )
        return {
            "primary_track_from": old_plan.get("primary_track"),
            "primary_track_to": new_plan.get("primary_track"),
            "weekly_objectives_added": sorted(new_obj - old_obj),
            "weekly_objectives_removed": sorted(old_obj - new_obj),
            "daily_action_changes": minute_deltas,
        }

    @staticmethod
    def _resolve_primary_track(profile: AssessmentProfile) -> str:
        value = str(profile.strategy_recommendation.get("primary_track", "主线A先行+主线B并行"))
        if value.strip():
            return value
        return "主线A先行+主线B并行"

    @staticmethod
    def _build_weekly_objectives(profile: AssessmentProfile, primary_track: str) -> list[str]:
        objectives = [
            "稳固防御底盘：单选/填空基础正确率优先",
            "扩展大题第一问覆盖：导数与解析几何基础问纳入可操作区",
            "执行多选保守残缺得分策略",
        ]
        weak_modules = [k for k, v in profile.module_mastery.items() if v in {"weak", "fragile"}]
        if weak_modules:
            objectives.append(f"本周优先修复薄弱模块：{', '.join(weak_modules[:3])}")
        if "主线A" in primary_track:
            objectives.append("主线A重点：向量-解三角形-立几建系的机械化流程")
        if "主线B" in primary_track:
            objectives.append("主线B重点：单位圆-诱导公式-整体换元")
        if profile.psychological_risk_level == "high":
            objectives.append("心理修复：每日建立微小成就反馈，避免黑名单题污染")
        return objectives

    def _build_daily_actions(
        self,
        profile: AssessmentProfile,
        primary_track: str,
        planning_horizon_days: int,
        daily_study_minutes: int,
    ) -> list[dict[str, object]]:
        actions: list[dict[str, object]] = []
        ratio_a = 0.6 if "主线A" in primary_track else 0.4
        if profile.defense_band == "foundation_rebuild":
            ratio_a = max(ratio_a, 0.65)
        ratio_a = min(0.75, max(0.35, ratio_a))
        minutes_a = int(daily_study_minutes * ratio_a)
        minutes_b = daily_study_minutes - minutes_a

        for day in range(1, planning_horizon_days + 1):
            # Every third day inserts a micro-review based on the "3-slice" mechanism.
            review_mode = "三题切片复评" if day % 3 == 0 else "常规训练"
            actions.append(
                {
                    "day": day,
                    "mode": review_mode,
                    "track_a_minutes": minutes_a,
                    "track_b_minutes": minutes_b,
                    "track_a_focus": self._pick_track_a_focus(day),
                    "track_b_focus": self._pick_track_b_focus(day),
                    "forbidden": ["压轴题深挖", "高复杂度含参分类讨论"],
                }
            )
        return actions

    @staticmethod
    def _pick_track_a_focus(day: int) -> str:
        focus_cycle = [
            "平面向量投影与数量积",
            "解三角形：正余弦定理机械化",
            "立体几何：找墙角建系与法向量",
        ]
        return focus_cycle[(day - 1) % len(focus_cycle)]

    @staticmethod
    def _pick_track_b_focus(day: int) -> str:
        focus_cycle = [
            "单位圆与弧度直观",
            "诱导公式图像推导",
            "整体换元与区间定界",
        ]
        return focus_cycle[(day - 1) % len(focus_cycle)]
