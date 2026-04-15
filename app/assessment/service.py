from __future__ import annotations

from dataclasses import asdict

from app.domain.models import AssessmentInput, AssessmentProfile


class AssessmentService:
    """MVP phase-1: learner assessment and initial defense strategy."""

    def run_assessment(self, assessment_input: AssessmentInput) -> AssessmentProfile:
        score_floor_estimate = self._estimate_score_floor(assessment_input)
        defense_band = self._build_defense_band(score_floor_estimate)
        cognitive_style_label = self._detect_cognitive_style(assessment_input)
        psychological_risk_level = self._detect_risk_level(assessment_input)
        module_mastery = self._build_module_mastery(assessment_input)
        strategy_recommendation = self._build_strategy_recommendation(
            defense_band=defense_band,
            cognitive_style_label=cognitive_style_label,
            risk_level=psychological_risk_level,
            weak_modules=assessment_input.weak_modules,
        )
        return AssessmentProfile(
            student_id=assessment_input.student_id,
            score_floor_estimate=round(score_floor_estimate, 2),
            defense_band=defense_band,
            cognitive_style_label=cognitive_style_label,
            psychological_risk_level=psychological_risk_level,
            module_mastery=module_mastery,
            strategy_recommendation=strategy_recommendation,
        )

    @staticmethod
    def serialize_profile(profile: AssessmentProfile) -> dict[str, object]:
        return asdict(profile)

    @staticmethod
    def _estimate_score_floor(assessment_input: AssessmentInput) -> float:
        # New-structure defensive pool uses 116 points (150 - 34 last two hard questions).
        single = 40 * _clamp_ratio(assessment_input.single_choice_accuracy)
        multi = 18 * _clamp_ratio(assessment_input.multi_choice_partial_accuracy)
        fill = 15 * _clamp_ratio(assessment_input.fill_blank_accuracy)
        big = 43 * _clamp_ratio(assessment_input.basic_big_question_accuracy)
        return min(116.0, single + multi + fill + big)

    @staticmethod
    def _build_defense_band(score_floor_estimate: float) -> str:
        if score_floor_estimate >= 92:
            return "stable_90_plus"
        if score_floor_estimate >= 80:
            return "rising_to_90"
        return "foundation_rebuild"

    @staticmethod
    def _detect_cognitive_style(assessment_input: AssessmentInput) -> str:
        if assessment_input.visual_preference_level >= 4 and assessment_input.symbolic_tolerance_level <= 2:
            return "visual_spatial_priority"
        if assessment_input.symbolic_tolerance_level >= 4:
            return "symbolic_tolerant"
        return "mixed_transition"

    @staticmethod
    def _detect_risk_level(assessment_input: AssessmentInput) -> str:
        pressure = _clamp_level(assessment_input.peer_pressure_level)
        helpless = _clamp_level(assessment_input.helplessness_level)
        time_penalty = 1.0 if assessment_input.daily_study_minutes < 90 else 0.0
        risk_score = pressure * 0.4 + helpless * 0.5 + time_penalty
        if risk_score >= 3.8:
            return "high"
        if risk_score >= 2.6:
            return "medium"
        return "low"

    @staticmethod
    def _build_module_mastery(assessment_input: AssessmentInput) -> dict[str, str]:
        all_modules = [
            "平面向量",
            "解三角形",
            "立体几何",
            "三角函数",
            "概率统计",
            "解析几何基础问",
            "导数基础问",
        ]
        weak_set = {module.strip() for module in assessment_input.weak_modules if module.strip()}
        base_accuracy = (
            _clamp_ratio(assessment_input.single_choice_accuracy)
            + _clamp_ratio(assessment_input.fill_blank_accuracy)
            + _clamp_ratio(assessment_input.basic_big_question_accuracy)
        ) / 3
        result: dict[str, str] = {}
        for module in all_modules:
            if module in weak_set:
                result[module] = "weak"
                continue
            if base_accuracy < 0.45:
                result[module] = "fragile"
            elif base_accuracy > 0.75:
                result[module] = "stable"
            else:
                result[module] = "maintain"
        return result

    @staticmethod
    def _build_strategy_recommendation(
        defense_band: str,
        cognitive_style_label: str,
        risk_level: str,
        weak_modules: list[str],
    ) -> dict[str, object]:
        primary_track = "主线A" if cognitive_style_label == "visual_spatial_priority" else "主线B"
        if cognitive_style_label == "mixed_transition":
            primary_track = "主线A先行+主线B并行"

        guard_policy = {
            "multi_choice_policy": "保守残缺得分",
            "must_cover": ["基础题", "解答题第一问广覆盖"],
            "forbidden": ["压轴题深挖", "高复杂度含参分类讨论"],
            "first_question_coverage": ["立体几何", "解三角形", "概率统计", "解析几何基础问", "导数基础问"],
        }
        if defense_band == "foundation_rebuild":
            guard_policy["must_cover"].append("单选与填空基础稳定")

        return {
            "primary_track": primary_track,
            "risk_action": "启动掌控感修复" if risk_level == "high" else "常规推进",
            "focus_modules": weak_modules[:3],
            "whitelist_modules": ["平面向量", "解三角形", "立体几何", "三角函数", "概率统计"],
            "blacklist_modules": ["压轴导数综合", "高难解析几何压轴", "复杂含参分类讨论"],
            "guard_policy": guard_policy,
        }


def _clamp_ratio(value: float) -> float:
    return max(0.0, min(1.0, value / 100.0))


def _clamp_level(value: int) -> int:
    return max(1, min(5, value))
