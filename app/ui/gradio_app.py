from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import gradio as gr

from app.application.container import build_container
from app.domain.models import AssessmentInput, AssessmentProfile, PlanningProfile, ProblemInput, SessionState
from app.review.service import ReviewInput


def build_app() -> gr.Blocks:
    container = build_container()

    def analyze_problem(question_text: str, student_attempt: str, student_question: str, image_file) -> tuple[str, str]:
        image_path = None
        if image_file is not None:
            image_path = str(Path(image_file))

        problem = ProblemInput(
            question_text=question_text,
            student_attempt=student_attempt,
            student_question=student_question,
            image_path=image_path,
        )
        response = container.tutor_service.handle_problem(problem, SessionState())
        session_id = container.store.create_session("local-demo-student", response.teaching_goal)
        container.store.add_turn(session_id, "student", question_text or "[empty question]")
        container.store.add_turn(session_id, "assistant", response.guiding_question)

        student_view = "\n".join(
            [
                f"问题理解：{response.problem_summary}",
                f"当前目标：{response.teaching_goal}",
                f"引导问题：{response.guiding_question}",
                f"视觉提示：{response.visual_hint}",
            ]
        )
        debug_view = json.dumps(
            {
                "information_sufficient": response.information_sufficient,
                "bug_type": response.bug_type,
                "teacher_note": response.teacher_note,
                "next_action": response.next_action,
                "session_id": session_id,
            },
            ensure_ascii=False,
            indent=2,
        )
        return student_view, debug_view

    def run_assessment(
        student_id: str,
        name_or_alias: str,
        target_score_range: str,
        daily_study_minutes: int,
        latest_math_score: float,
        single_choice_accuracy: float,
        multi_choice_partial_accuracy: float,
        fill_blank_accuracy: float,
        basic_big_question_accuracy: float,
        visual_preference_level: int,
        symbolic_tolerance_level: int,
        peer_pressure_level: int,
        helplessness_level: int,
        weak_modules_text: str,
    ) -> tuple[str, str]:
        weak_modules = [item.strip() for item in weak_modules_text.split(",") if item.strip()]
        if not student_id.strip():
            student_id = "local-demo-student"
        if not name_or_alias.strip():
            name_or_alias = "未命名学生"

        assessment_input = AssessmentInput(
            student_id=student_id.strip(),
            name_or_alias=name_or_alias.strip(),
            target_score_range=target_score_range.strip() or "90-100",
            daily_study_minutes=int(daily_study_minutes),
            latest_math_score=float(latest_math_score),
            single_choice_accuracy=float(single_choice_accuracy),
            multi_choice_partial_accuracy=float(multi_choice_partial_accuracy),
            fill_blank_accuracy=float(fill_blank_accuracy),
            basic_big_question_accuracy=float(basic_big_question_accuracy),
            visual_preference_level=int(visual_preference_level),
            symbolic_tolerance_level=int(symbolic_tolerance_level),
            peer_pressure_level=int(peer_pressure_level),
            helplessness_level=int(helplessness_level),
            weak_modules=weak_modules,
        )
        profile = container.assessment_service.run_assessment(assessment_input)
        serialized = container.assessment_service.serialize_profile(profile)

        container.store.upsert_student(
            student_id=assessment_input.student_id,
            name_or_alias=assessment_input.name_or_alias,
            target_score_range=assessment_input.target_score_range,
        )
        assessment_profile_id = container.store.save_assessment_profile(
            student_id=profile.student_id,
            score_floor_estimate=profile.score_floor_estimate,
            defense_band=profile.defense_band,
            cognitive_style_label=profile.cognitive_style_label,
            psychological_risk_level=profile.psychological_risk_level,
            module_mastery=profile.module_mastery,
            strategy_recommendation=profile.strategy_recommendation,
        )
        summary = "\n".join(
            [
                f"学生：{assessment_input.name_or_alias}（{assessment_input.student_id}）",
                f"防御底盘估计：{profile.score_floor_estimate:.1f} / 116",
                f"防御分层：{profile.defense_band}",
                f"认知风格：{profile.cognitive_style_label}",
                f"心理风险等级：{profile.psychological_risk_level}",
                f"主线建议：{profile.strategy_recommendation.get('primary_track', '未生成')}",
                f"评估记录ID：{assessment_profile_id}",
            ]
        )
        return summary, json.dumps(serialized, ensure_ascii=False, indent=2)

    def generate_plan(
        assessment_profile_json: str,
        planning_horizon_days: int,
        daily_study_minutes: int,
    ) -> tuple[str, str]:
        if not assessment_profile_json.strip():
            return "请先完成学情评估，再生成计划。", "{}"
        try:
            payload = json.loads(assessment_profile_json)
            profile = AssessmentProfile(
                student_id=str(payload["student_id"]),
                score_floor_estimate=float(payload["score_floor_estimate"]),
                defense_band=str(payload["defense_band"]),
                cognitive_style_label=str(payload["cognitive_style_label"]),
                psychological_risk_level=str(payload["psychological_risk_level"]),
                module_mastery=dict(payload["module_mastery"]),
                strategy_recommendation=dict(payload["strategy_recommendation"]),
            )
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return "画像结构解析失败，请重新执行学情评估。", "{}"

        plan = container.planning_service.generate_plan(
            profile=profile,
            planning_horizon_days=int(planning_horizon_days),
            daily_study_minutes=int(daily_study_minutes),
        )
        serialized = container.planning_service.serialize_plan(plan)
        plan_version_id = container.store.save_plan_version(
            student_id=plan.student_id,
            planning_horizon_days=plan.planning_horizon_days,
            plan_json=serialized,
            change_reason="assessment_phase2_initial_plan",
        )
        summary = "\n".join(
            [
                f"学生ID：{plan.student_id}",
                f"计划周期：{plan.planning_horizon_days} 天",
                f"主线策略：{plan.primary_track}",
                f"风险动作：{plan.risk_action}",
                f"周目标数：{len(plan.weekly_objectives)}",
                f"日任务条目：{len(plan.daily_actions)}",
                f"计划版本ID：{plan_version_id}",
            ]
        )
        return summary, json.dumps(serialized, ensure_ascii=False, indent=2)

    def run_review_and_repair(
        assessment_profile_json: str,
        visual_reconstruction_score: float,
        mechanical_execution_score: float,
        feynman_explain_score: float,
        target_node: str,
    ) -> tuple[str, str, str]:
        if not assessment_profile_json.strip():
            return "请先完成学情评估。", "{}", "{}"
        try:
            payload = json.loads(assessment_profile_json)
            student_id = str(payload["student_id"])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return "画像结构解析失败。", "{}", "{}"

        review_input = ReviewInput(
            student_id=student_id,
            visual_reconstruction_score=float(visual_reconstruction_score),
            mechanical_execution_score=float(mechanical_execution_score),
            feynman_explain_score=float(feynman_explain_score),
            target_node=target_node.strip() or "通用节点",
        )
        review_result = container.review_service.evaluate(review_input)
        review_run_id = container.store.save_review_run(
            student_id=review_result.student_id,
            target_node=review_result.target_node,
            review_score=review_result.review_score,
            pass_status=review_result.pass_status,
            trigger_repair=review_result.trigger_repair,
            suggested_action=review_result.suggested_action,
        )
        review_payload = container.review_service.serialize(review_result)

        protocol_payload: dict[str, object] = {}
        if review_result.trigger_repair:
            protocol_payload = container.repair_service.get_protocol(review_result.target_node)
            repair_event_id = container.store.save_repair_event(
                student_id=review_result.student_id,
                target_node=review_result.target_node,
                protocol_id=str(protocol_payload.get("protocol_id", "RP-GENERIC")),
                protocol=protocol_payload,
            )
            protocol_payload["repair_event_id"] = repair_event_id

        summary = "\n".join(
            [
                f"复评记录ID：{review_run_id}",
                f"复评分数：{review_result.review_score}",
                f"通过状态：{review_result.pass_status}",
                f"是否触发修复：{'是' if review_result.trigger_repair else '否'}",
                f"建议动作：{review_result.suggested_action}",
            ]
        )
        return (
            summary,
            json.dumps(review_payload, ensure_ascii=False, indent=2),
            json.dumps(protocol_payload, ensure_ascii=False, indent=2),
        )

    def build_parent_dashboard(
        assessment_profile_json: str,
        planning_profile_json: str,
        day_index: int,
    ) -> tuple[str, str]:
        if not assessment_profile_json.strip() or not planning_profile_json.strip():
            return "请先生成学情画像和日周计划。", "{}"
        try:
            assessment_payload = json.loads(assessment_profile_json)
            planning_payload = json.loads(planning_profile_json)
            assessment_profile = AssessmentProfile(
                student_id=str(assessment_payload["student_id"]),
                score_floor_estimate=float(assessment_payload["score_floor_estimate"]),
                defense_band=str(assessment_payload["defense_band"]),
                cognitive_style_label=str(assessment_payload["cognitive_style_label"]),
                psychological_risk_level=str(assessment_payload["psychological_risk_level"]),
                module_mastery=dict(assessment_payload["module_mastery"]),
                strategy_recommendation=dict(assessment_payload["strategy_recommendation"]),
            )
            planning_profile = PlanningProfile(
                student_id=str(planning_payload["student_id"]),
                planning_horizon_days=int(planning_payload["planning_horizon_days"]),
                primary_track=str(planning_payload["primary_track"]),
                weekly_objectives=list(planning_payload["weekly_objectives"]),
                daily_actions=list(planning_payload["daily_actions"]),
                guard_policy=dict(planning_payload["guard_policy"]),
                risk_action=str(planning_payload["risk_action"]),
            )
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return "计划或画像结构解析失败。", "{}"

        dashboard = container.parent_dashboard_service.build_dashboard(
            assessment_profile=assessment_profile,
            planning_profile=planning_profile,
            day_index=int(day_index),
        )
        summary = "\n".join(
            [
                f"学生ID：{dashboard['student_id']}",
                f"第 {dashboard['day']} 天模式：{dashboard['today_mode']}",
                f"今日重点：{', '.join(dashboard['today_focus'])}",
                f"禁练项：{', '.join(dashboard['forbidden_items'])}",
                f"鼓励话术：{dashboard['encouragement']}",
                f"风险提醒：{dashboard['risk_alert']}",
            ]
        )
        return summary, json.dumps(dashboard, ensure_ascii=False, indent=2)

    def auto_tune_plan_from_review(
        assessment_profile_json: str,
        planning_profile_json: str,
        review_result_json: str,
        daily_study_minutes: int,
    ) -> tuple[str, str, str]:
        if not assessment_profile_json.strip() or not planning_profile_json.strip() or not review_result_json.strip():
            return "请先生成画像、计划并完成复评。", "{}", "{}"
        try:
            assessment_payload = json.loads(assessment_profile_json)
            planning_payload = json.loads(planning_profile_json)
            review_payload = json.loads(review_result_json)

            assessment_profile = AssessmentProfile(
                student_id=str(assessment_payload["student_id"]),
                score_floor_estimate=float(assessment_payload["score_floor_estimate"]),
                defense_band=str(assessment_payload["defense_band"]),
                cognitive_style_label=str(assessment_payload["cognitive_style_label"]),
                psychological_risk_level=str(assessment_payload["psychological_risk_level"]),
                module_mastery=dict(assessment_payload["module_mastery"]),
                strategy_recommendation=dict(assessment_payload["strategy_recommendation"]),
            )
            planning_profile = PlanningProfile(
                student_id=str(planning_payload["student_id"]),
                planning_horizon_days=int(planning_payload["planning_horizon_days"]),
                primary_track=str(planning_payload["primary_track"]),
                weekly_objectives=list(planning_payload["weekly_objectives"]),
                daily_actions=list(planning_payload["daily_actions"]),
                guard_policy=dict(planning_payload["guard_policy"]),
                risk_action=str(planning_payload["risk_action"]),
            )
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return "输入结构解析失败。", "{}", "{}"

        new_plan = container.planning_service.replan_after_review(
            profile=assessment_profile,
            current_plan=planning_profile,
            review_payload=review_payload,
            daily_study_minutes=int(daily_study_minutes),
        )
        new_payload = container.planning_service.serialize_plan(new_plan)
        diff_payload = container.planning_service.diff_plan_payloads(planning_payload, new_payload)

        new_plan_version_id = container.store.save_plan_version(
            student_id=new_plan.student_id,
            planning_horizon_days=new_plan.planning_horizon_days,
            plan_json=new_payload,
            change_reason="auto_tune_after_review",
        )
        summary = "\n".join(
            [
                f"自动调参完成：计划版本ID={new_plan_version_id}",
                f"复评状态：{review_payload.get('pass_status', 'unknown')}",
                f"触发修复：{'是' if review_payload.get('trigger_repair', False) else '否'}",
                f"新增周目标：{len(diff_payload.get('weekly_objectives_added', []))}",
                f"日任务调整项：{len(diff_payload.get('daily_action_changes', []))}",
            ]
        )
        return summary, json.dumps(new_payload, ensure_ascii=False, indent=2), json.dumps(diff_payload, ensure_ascii=False, indent=2)

    def compare_latest_plan_versions(student_id: str) -> tuple[str, str]:
        sid = student_id.strip() or "local-demo-student"
        versions = container.store.get_latest_two_plan_versions(sid)
        if len(versions) < 2:
            return "该学生至少需要两版计划后才能对比。", "{}"

        latest = versions[0]
        previous = versions[1]
        diff_payload = container.planning_service.diff_plan_payloads(previous["plan_json"], latest["plan_json"])
        summary = "\n".join(
            [
                f"学生ID：{sid}",
                f"最新版本：{latest['plan_version_id']}（{latest['change_reason']}）",
                f"上一版本：{previous['plan_version_id']}（{previous['change_reason']}）",
                f"新增周目标：{len(diff_payload.get('weekly_objectives_added', []))}",
                f"移除周目标：{len(diff_payload.get('weekly_objectives_removed', []))}",
                f"日任务调整：{len(diff_payload.get('daily_action_changes', []))}",
            ]
        )
        return summary, json.dumps(diff_payload, ensure_ascii=False, indent=2)

    def save_parent_checkin(
        assessment_profile_json: str,
        planning_profile_json: str,
        day_index: int,
        completed: bool,
        note: str,
    ) -> str:
        summary, dashboard_json = build_parent_dashboard(assessment_profile_json, planning_profile_json, day_index)
        if dashboard_json == "{}":
            return "家长面板未生成，无法打卡。"
        dashboard_payload = json.loads(dashboard_json)
        checkin_id = container.store.save_parent_checkin(
            student_id=str(dashboard_payload.get("student_id", "local-demo-student")),
            day_index=int(dashboard_payload.get("day", day_index)),
            completed=bool(completed),
            note=note.strip(),
            dashboard_payload=dashboard_payload,
        )
        return f"打卡已保存，checkin_id={checkin_id}，完成状态={'完成' if completed else '未完成'}"

    def build_review_trend_report(student_id: str) -> tuple[str, str]:
        sid = student_id.strip() or "local-demo-student"
        review_runs = container.store.list_recent_review_runs(sid, limit=30)
        trend = container.reporting_service.build_review_trend(sid, review_runs)
        payload = container.reporting_service.serialize_trend(trend)
        summary = "\n".join(
            [
                f"学生ID：{sid}",
                f"样本数：{payload['sample_size']}",
                f"平均分：{payload['average_score']}",
                f"最新分：{payload['latest_score']}",
                f"通过率：{payload['pass_rate']}",
                f"修复触发率：{payload['repair_trigger_rate']}",
                f"趋势判断：{payload['risk_trend']}",
            ]
        )
        return summary, json.dumps(payload, ensure_ascii=False, indent=2)

    def build_parent_weekly_report(student_id: str, max_days: int) -> tuple[str, str]:
        sid = student_id.strip() or "local-demo-student"
        checkins = container.store.list_parent_checkins(sid, limit=int(max_days))
        payload = container.reporting_service.build_parent_weekly_report(sid, checkins, max_days=int(max_days))
        summary = "\n".join(
            [
                f"学生ID：{sid}",
                f"统计天数：{payload['days']}",
                f"完成率：{payload['completion_rate']}",
                f"亮点数量：{len(payload['highlights'])}",
                f"风险提示数量：{len(payload['risks'])}",
            ]
        )
        return summary, json.dumps(payload, ensure_ascii=False, indent=2)

    def export_student_snapshot(student_id: str) -> tuple[str, str]:
        sid = student_id.strip() or "local-demo-student"
        latest_assessment = container.store.get_latest_assessment_profile(sid)
        latest_plan = container.store.get_latest_plan_version(sid)
        review_runs = container.store.list_recent_review_runs(sid, limit=30)
        checkins = container.store.list_parent_checkins(sid, limit=30)
        payload = container.reporting_service.export_snapshot(
            student_id=sid,
            latest_assessment=latest_assessment,
            latest_plan=latest_plan,
            review_runs=review_runs,
            checkins=checkins,
        )
        summary = "\n".join(
            [
                f"学生ID：{sid}",
                f"画像是否存在：{'是' if payload.get('latest_assessment') else '否'}",
                f"计划是否存在：{'是' if payload.get('latest_plan') else '否'}",
                f"复评样本数：{len(payload.get('review_samples', []))}",
                f"打卡样本数：{len(payload.get('checkin_samples', []))}",
            ]
        )
        return summary, json.dumps(payload, ensure_ascii=False, indent=2)

    def build_alerts_and_chart(student_id: str) -> tuple[str, str, str]:
        sid = student_id.strip() or "local-demo-student"
        review_runs = container.store.list_recent_review_runs(sid, limit=30)
        checkins = container.store.list_parent_checkins(sid, limit=14)
        trend = container.reporting_service.serialize_trend(
            container.reporting_service.build_review_trend(sid, review_runs)
        )
        weekly = container.reporting_service.build_parent_weekly_report(sid, checkins, max_days=7)
        thresholds = container.store.get_alert_thresholds(sid)
        alerts = container.reporting_service.build_threshold_alerts(trend, weekly, thresholds=thresholds)
        chart_payload = container.reporting_service.build_chart_payload(review_runs, checkins)
        chart_html = container.reporting_service.build_simple_chart_html(chart_payload)
        return "\n".join(alerts), json.dumps(chart_payload, ensure_ascii=False, indent=2), chart_html

    def save_alert_thresholds(
        student_id: str,
        latest_score_min: float,
        pass_rate_min: float,
        repair_rate_max: float,
        completion_rate_min: float,
    ) -> str:
        sid = student_id.strip() or "local-demo-student"
        container.store.upsert_alert_thresholds(
            student_id=sid,
            latest_score_min=float(latest_score_min),
            pass_rate_min=float(pass_rate_min),
            repair_rate_max=float(repair_rate_max),
            completion_rate_min=float(completion_rate_min),
        )
        return f"阈值配置已保存：{sid}"

    def export_snapshot_files(student_id: str) -> tuple[str, str, str]:
        sid = student_id.strip() or "local-demo-student"
        _, snapshot_json = export_student_snapshot(sid)
        snapshot = json.loads(snapshot_json)
        markdown_text = container.reporting_service.to_markdown_snapshot(snapshot)

        export_dir = Path("data") / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = export_dir / f"{sid}_snapshot_{stamp}.json"
        md_path = export_dir / f"{sid}_snapshot_{stamp}.md"
        json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(markdown_text, encoding="utf-8")
        summary = "\n".join(
            [
                f"导出完成：{sid}",
                f"JSON：{json_path}",
                f"Markdown：{md_path}",
            ]
        )
        return summary, str(json_path), str(md_path)

    def bulk_export_weekly_reports(max_days: int) -> tuple[str, str, str]:
        students = container.store.list_students()
        payloads: list[dict[str, object]] = []
        md_lines = ["# 批量周报导出", ""]
        for student in students:
            sid = student["student_id"]
            checkins = container.store.list_parent_checkins(sid, limit=int(max_days))
            weekly = container.reporting_service.build_parent_weekly_report(sid, checkins, max_days=int(max_days))
            payloads.append({"student_id": sid, "weekly_report": weekly})
            md_lines.extend(
                [
                    f"## {sid}",
                    f"- 完成率：{weekly.get('completion_rate', 0)}",
                    f"- 风险：{'; '.join(weekly.get('risks', []))}",
                    "",
                ]
            )

        bulk = container.reporting_service.build_bulk_weekly_export(payloads)
        export_dir = Path("data") / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = export_dir / f"bulk_weekly_{stamp}.json"
        md_path = export_dir / f"bulk_weekly_{stamp}.md"
        json_path.write_text(json.dumps(bulk, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        summary = f"批量周报导出完成，学生数={bulk.get('student_count', 0)}"
        return summary, str(json_path), str(md_path)

    def build_ops_dashboard() -> tuple[str, str]:
        metrics = container.store.get_system_metrics()
        gaps = container.store.get_data_quality_gaps()
        payload = container.ops_service.build_dashboard(metrics, gaps)
        summary = "\n".join(
            [
                f"学生数：{metrics.get('students_count', 0)}",
                f"画像数：{metrics.get('assessment_profiles_count', 0)}",
                f"计划数：{metrics.get('plan_versions_count', 0)}",
                f"复评数：{metrics.get('review_runs_count', 0)}",
                f"打卡数：{metrics.get('parent_checkins_count', 0)}",
                f"巡检告警数：{len(payload.get('alerts', []))}",
            ]
        )
        return summary, json.dumps(payload, ensure_ascii=False, indent=2)

    with gr.Blocks(title="HightSchoolMathAgent M1 MVP") as demo:
        gr.Markdown(
            """
            # HightSchoolMathAgent M1 本地 MVP

            当前版本是代码骨架：
            - 使用 `FakeTutorModelAdapter` 跑通主链路；
            - 支持文本输入与图片占位接入；
            - 支持最基础的错因归因、引导输出与 SQLite 会话记录。
            - 支持 MVP 第一阶段的学情评估与防御策略初始化。
            """
        )

        with gr.Tabs():
            with gr.TabItem("题目诊断"):
                with gr.Row():
                    question_text = gr.Textbox(label="题目内容", lines=6, placeholder="粘贴题干或手动转写题目")
                    student_attempt = gr.Textbox(label="你的尝试", lines=6, placeholder="写你做到哪一步")

                with gr.Row():
                    student_question = gr.Textbox(label="你卡住的点", lines=3, placeholder="比如：为什么这里能用余弦定理？")
                    image_file = gr.File(label="题目图片（占位）", file_count="single")

                analyze_button = gr.Button("开始诊断")

                with gr.Row():
                    student_output = gr.Textbox(label="学生视角输出", lines=10)
                    debug_output = gr.Code(label="结构化调试输出", language="json")

                analyze_button.click(
                    fn=analyze_problem,
                    inputs=[question_text, student_attempt, student_question, image_file],
                    outputs=[student_output, debug_output],
                )

            with gr.TabItem("学情评估"):
                with gr.Row():
                    student_id = gr.Textbox(label="学生ID", value="local-demo-student")
                    name_or_alias = gr.Textbox(label="学生称呼", value="演示学生")
                    target_score_range = gr.Textbox(label="目标分数区间", value="90-100")

                with gr.Row():
                    daily_study_minutes = gr.Number(label="每日可投入分钟", value=120, minimum=30, maximum=360)
                    latest_math_score = gr.Number(label="最近数学成绩", value=62, minimum=0, maximum=150)

                with gr.Row():
                    single_choice_accuracy = gr.Slider(
                        label="单选正确率(%)",
                        minimum=0,
                        maximum=100,
                        value=65,
                        step=1,
                    )
                    multi_choice_partial_accuracy = gr.Slider(
                        label="多选可得分率(%)",
                        minimum=0,
                        maximum=100,
                        value=45,
                        step=1,
                    )
                with gr.Row():
                    fill_blank_accuracy = gr.Slider(
                        label="填空正确率(%)",
                        minimum=0,
                        maximum=100,
                        value=40,
                        step=1,
                    )
                    basic_big_question_accuracy = gr.Slider(
                        label="大题基础问得分率(%)",
                        minimum=0,
                        maximum=100,
                        value=38,
                        step=1,
                    )

                with gr.Row():
                    visual_preference_level = gr.Slider(
                        label="视觉偏好等级(1-5)",
                        minimum=1,
                        maximum=5,
                        value=4,
                        step=1,
                    )
                    symbolic_tolerance_level = gr.Slider(
                        label="符号推导耐受度(1-5)",
                        minimum=1,
                        maximum=5,
                        value=2,
                        step=1,
                    )

                with gr.Row():
                    peer_pressure_level = gr.Slider(
                        label="同侪压力等级(1-5)",
                        minimum=1,
                        maximum=5,
                        value=4,
                        step=1,
                    )
                    helplessness_level = gr.Slider(
                        label="无助感等级(1-5)",
                        minimum=1,
                        maximum=5,
                        value=3,
                        step=1,
                    )

                weak_modules_text = gr.Textbox(
                    label="薄弱模块（逗号分隔）",
                    value="立体几何,三角函数,导数基础问",
                    placeholder="例如：平面向量,立体几何,三角函数",
                )
                run_assessment_button = gr.Button("生成学情画像")

                with gr.Row():
                    assessment_summary = gr.Textbox(label="评估摘要", lines=10)
                    assessment_debug = gr.Code(label="画像结构化输出", language="json")

                run_assessment_button.click(
                    fn=run_assessment,
                    inputs=[
                        student_id,
                        name_or_alias,
                        target_score_range,
                        daily_study_minutes,
                        latest_math_score,
                        single_choice_accuracy,
                        multi_choice_partial_accuracy,
                        fill_blank_accuracy,
                        basic_big_question_accuracy,
                        visual_preference_level,
                        symbolic_tolerance_level,
                        peer_pressure_level,
                        helplessness_level,
                        weak_modules_text,
                    ],
                    outputs=[assessment_summary, assessment_debug],
                )

                gr.Markdown("### 个性化补习计划（第二批实现）")
                with gr.Row():
                    planning_horizon_days = gr.Slider(
                        label="计划周期(天)",
                        minimum=7,
                        maximum=28,
                        value=14,
                        step=1,
                    )
                    planning_daily_minutes = gr.Number(
                        label="计划按每天分钟数",
                        value=120,
                        minimum=45,
                        maximum=300,
                    )
                run_planning_button = gr.Button("生成日周计划")
                with gr.Row():
                    planning_summary = gr.Textbox(label="计划摘要", lines=8)
                    planning_debug = gr.Code(label="计划结构化输出", language="json")

                run_planning_button.click(
                    fn=generate_plan,
                    inputs=[assessment_debug, planning_horizon_days, planning_daily_minutes],
                    outputs=[planning_summary, planning_debug],
                )

                gr.Markdown("### 三题切片复评与熔断修复（第三批实现）")
                with gr.Row():
                    visual_reconstruction_score = gr.Slider(
                        label="视觉复现题得分(0-100)",
                        minimum=0,
                        maximum=100,
                        value=68,
                        step=1,
                    )
                    mechanical_execution_score = gr.Slider(
                        label="机械执行题得分(0-100)",
                        minimum=0,
                        maximum=100,
                        value=64,
                        step=1,
                    )
                    feynman_explain_score = gr.Slider(
                        label="费曼讲解题得分(0-100)",
                        minimum=0,
                        maximum=100,
                        value=58,
                        step=1,
                    )
                target_node = gr.Dropdown(
                    label="复评目标节点",
                    choices=["整体换元", "立体建系", "通用节点"],
                    value="整体换元",
                )
                run_review_button = gr.Button("执行复评并判定修复")
                with gr.Row():
                    review_summary = gr.Textbox(label="复评摘要", lines=8)
                    review_debug = gr.Code(label="复评结构化输出", language="json")
                    repair_debug = gr.Code(label="修复协议输出", language="json")

                run_review_button.click(
                    fn=run_review_and_repair,
                    inputs=[
                        assessment_debug,
                        visual_reconstruction_score,
                        mechanical_execution_score,
                        feynman_explain_score,
                        target_node,
                    ],
                    outputs=[review_summary, review_debug, repair_debug],
                )

                gr.Markdown("### 自动调参与版本对比（第四批实现）")
                auto_tune_button = gr.Button("根据复评自动调参并生成新版本")
                with gr.Row():
                    auto_tune_summary = gr.Textbox(label="调参摘要", lines=8)
                    auto_tuned_plan_debug = gr.Code(label="调参后计划输出", language="json")
                    auto_tune_diff_debug = gr.Code(label="与上一版差异", language="json")

                auto_tune_button.click(
                    fn=auto_tune_plan_from_review,
                    inputs=[assessment_debug, planning_debug, review_debug, planning_daily_minutes],
                    outputs=[auto_tune_summary, auto_tuned_plan_debug, auto_tune_diff_debug],
                )

                compare_plan_button = gr.Button("对比最近两版计划")
                with gr.Row():
                    compare_plan_summary = gr.Textbox(label="版本对比摘要", lines=8)
                    compare_plan_debug = gr.Code(label="版本差异输出", language="json")
                compare_plan_button.click(
                    fn=compare_latest_plan_versions,
                    inputs=[student_id],
                    outputs=[compare_plan_summary, compare_plan_debug],
                )

                gr.Markdown("### 家长执行面板（第三批实现）")
                parent_day_index = gr.Slider(label="查看第几天执行建议", minimum=1, maximum=28, value=1, step=1)
                run_parent_dashboard_button = gr.Button("生成家长执行面板")
                with gr.Row():
                    parent_summary = gr.Textbox(label="家长面板摘要", lines=8)
                    parent_debug = gr.Code(label="家长面板结构化输出", language="json")

                run_parent_dashboard_button.click(
                    fn=build_parent_dashboard,
                    inputs=[assessment_debug, planning_debug, parent_day_index],
                    outputs=[parent_summary, parent_debug],
                )

                with gr.Row():
                    parent_completed = gr.Checkbox(label="今日计划是否完成", value=True)
                    parent_note = gr.Textbox(label="家长备注", placeholder="例如：立体建系仍需慢速复练")
                save_parent_checkin_button = gr.Button("保存家长打卡")
                parent_checkin_result = gr.Textbox(label="打卡结果", lines=3)
                save_parent_checkin_button.click(
                    fn=save_parent_checkin,
                    inputs=[assessment_debug, planning_debug, parent_day_index, parent_completed, parent_note],
                    outputs=[parent_checkin_result],
                )

                gr.Markdown("### 趋势与周报（第五批实现）")
                with gr.Row():
                    trend_summary = gr.Textbox(label="复评趋势摘要", lines=8)
                    trend_debug = gr.Code(label="复评趋势结构化输出", language="json")
                build_trend_button = gr.Button("生成复评趋势报告")
                build_trend_button.click(
                    fn=build_review_trend_report,
                    inputs=[student_id],
                    outputs=[trend_summary, trend_debug],
                )

                weekly_days = gr.Slider(label="家长周报统计天数", minimum=3, maximum=14, value=7, step=1)
                with gr.Row():
                    weekly_summary = gr.Textbox(label="家长周报摘要", lines=8)
                    weekly_debug = gr.Code(label="家长周报结构化输出", language="json")
                build_weekly_report_button = gr.Button("生成家长周报")
                build_weekly_report_button.click(
                    fn=build_parent_weekly_report,
                    inputs=[student_id, weekly_days],
                    outputs=[weekly_summary, weekly_debug],
                )

                gr.Markdown("### 学习快照导出（第五批实现）")
                with gr.Row():
                    snapshot_summary = gr.Textbox(label="快照摘要", lines=8)
                    snapshot_debug = gr.Code(label="快照结构化输出", language="json")
                export_snapshot_button = gr.Button("导出学习快照")
                export_snapshot_button.click(
                    fn=export_student_snapshot,
                    inputs=[student_id],
                    outputs=[snapshot_summary, snapshot_debug],
                )

                gr.Markdown("### 图表与告警（第六批实现）")
                with gr.Row():
                    alert_latest_score_min = gr.Number(label="阈值：最新分最低", value=60, minimum=0, maximum=100)
                    alert_pass_rate_min = gr.Number(label="阈值：通过率最低(0-1)", value=0.5, minimum=0, maximum=1)
                with gr.Row():
                    alert_repair_rate_max = gr.Number(label="阈值：修复触发率最高(0-1)", value=0.5, minimum=0, maximum=1)
                    alert_completion_rate_min = gr.Number(label="阈值：完成率最低(0-1)", value=0.6, minimum=0, maximum=1)
                save_threshold_button = gr.Button("保存告警阈值配置")
                save_threshold_result = gr.Textbox(label="阈值配置结果", lines=2)
                save_threshold_button.click(
                    fn=save_alert_thresholds,
                    inputs=[student_id, alert_latest_score_min, alert_pass_rate_min, alert_repair_rate_max, alert_completion_rate_min],
                    outputs=[save_threshold_result],
                )

                build_alert_button = gr.Button("生成阈值告警与趋势图")
                with gr.Row():
                    alert_summary = gr.Textbox(label="阈值告警", lines=6)
                    chart_debug = gr.Code(label="图表数据结构", language="json")
                chart_html = gr.HTML(label="趋势可视化")
                build_alert_button.click(
                    fn=build_alerts_and_chart,
                    inputs=[student_id],
                    outputs=[alert_summary, chart_debug, chart_html],
                )

                gr.Markdown("### 文件导出（第六批实现）")
                export_files_button = gr.Button("导出 JSON + Markdown 文件")
                export_files_summary = gr.Textbox(label="导出结果", lines=4)
                export_json_file = gr.File(label="下载 JSON 快照")
                export_md_file = gr.File(label="下载 Markdown 快照")
                export_files_button.click(
                    fn=export_snapshot_files,
                    inputs=[student_id],
                    outputs=[export_files_summary, export_json_file, export_md_file],
                )

                gr.Markdown("### 批量导出与运维巡检（第七至第十批实现）")
                bulk_days = gr.Slider(label="批量周报统计天数", minimum=3, maximum=30, value=7, step=1)
                bulk_export_button = gr.Button("批量导出全部学生周报")
                bulk_export_summary = gr.Textbox(label="批量导出结果", lines=3)
                bulk_json_file = gr.File(label="下载批量JSON")
                bulk_md_file = gr.File(label="下载批量Markdown")
                bulk_export_button.click(
                    fn=bulk_export_weekly_reports,
                    inputs=[bulk_days],
                    outputs=[bulk_export_summary, bulk_json_file, bulk_md_file],
                )

                ops_button = gr.Button("生成系统运维看板")
                with gr.Row():
                    ops_summary = gr.Textbox(label="运维摘要", lines=6)
                    ops_debug = gr.Code(label="运维结构化输出", language="json")
                ops_button.click(
                    fn=build_ops_dashboard,
                    inputs=[],
                    outputs=[ops_summary, ops_debug],
                )

    return demo
