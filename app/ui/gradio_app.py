from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from app.application.container import build_container
from app.domain.models import ProblemInput, SessionState


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

    with gr.Blocks(title="HightSchoolMathAgent M1 MVP") as demo:
        gr.Markdown(
            """
            # HightSchoolMathAgent M1 本地 MVP

            当前版本是代码骨架：
            - 使用 `FakeTutorModelAdapter` 跑通主链路；
            - 支持文本输入与图片占位接入；
            - 支持最基础的错因归因、引导输出与 SQLite 会话记录。
            """
        )

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

    return demo
