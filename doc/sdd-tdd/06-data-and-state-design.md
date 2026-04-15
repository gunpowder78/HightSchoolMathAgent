# 数据与状态设计

## 1. 设计目标

数据与状态层必须支持以下能力：

- 支持单用户本地 MVP 稳定运行。
- 支持错题本、学习画像、家长报告等核心闭环。
- 支持多轮会话状态压缩与恢复。
- 为后续向量记忆、双脑架构、实时接力预留扩展点。

## 2. 领域对象

### 2.1 StudentProfile

字段建议：

- `student_id`
- `name_or_alias`
- `grade`
- `province`
- `exam_track`
- `target_score_range`
- `weak_modules`
- `blacklist_modules`
- `whitelist_modules`
- `available_schedule`
- `created_at`
- `updated_at`

### 2.2 ProblemRecord

字段建议：

- `problem_id`
- `student_id`
- `source_type`，如 text/image/live_frame
- `raw_text`
- `image_blob_ref`
- `topic`
- `subtopic`
- `difficulty_band`
- `whitelist_status`
- `created_at`

### 2.3 Session

字段建议：

- `session_id`
- `student_id`
- `mode`，如 async/live
- `status`
- `current_goal`
- `current_bug_type`
- `summary_state`
- `started_at`
- `ended_at`

### 2.4 Turn

字段建议：

- `turn_id`
- `session_id`
- `role`
- `input_type`
- `content`
- `structured_output_json`
- `latency_ms`
- `created_at`

### 2.5 ErrorDiagnosis

字段建议：

- `diagnosis_id`
- `problem_id`
- `session_id`
- `bug_type`
- `bug_subtype`
- `evidence`
- `confidence`
- `recommended_action`
- `created_at`

### 2.6 PracticeRecord

字段建议：

- `practice_id`
- `problem_id`
- `student_id`
- `practice_type`
- `generator_version`
- `difficulty_guard`
- `result`
- `mistake_summary`
- `created_at`

### 2.7 WeeklyReport

字段建议：

- `report_id`
- `student_id`
- `date_range`
- `high_frequency_bugs`
- `recommended_modules`
- `risk_alerts`
- `next_actions`
- `created_at`

## 3. MVP 存储方案

### 3.1 推荐方案

- 主库：`SQLite`
- 模式：`WAL`
- 图片：可先存 BLOB 或统一文件引用

### 3.2 理由

- 简单、稳定、适合单机。
- 支持结构化查询。
- 便于后续迁移到 `PostgreSQL`。

## 4. 会话状态对象

会话状态建议独立为结构化对象，而不是只依赖原始聊天记录。

建议字段：

- `known_conditions`
- `missing_information`
- `student_current_step`
- `bug_type`
- `rejected_paths`
- `current_teaching_goal`
- `next_allowed_actions`
- `scaffold_level`
- `summary_for_next_round`

## 5. 会话状态机

建议定义以下状态：

- `created`
- `awaiting_input`
- `clarifying`
- `diagnosing`
- `guiding`
- `scaffolding`
- `practice`
- `summarizing`
- `closed`
- `failed`

状态迁移原则：

- 信息不足时必须进入 `clarifying`。
- 连续失败后才进入 `scaffolding`。
- 完成当前认知点后才进入 `practice` 或 `summarizing`。

## 6. 会话摘要机制

### 6.1 触发条件

- 对话达到固定轮次。
- Token 预算接近阈值。
- 模式从异步切换到实时或从实时切换到异步。

### 6.2 摘要内容

- 当前问题是什么。
- 已确认的条件有哪些。
- 学生目前错在哪里。
- 已经尝试过哪些引导。
- 下一轮最该做什么。

## 7. 图片与实时关键帧设计

### 7.1 图片记录

至少存储：

- 原始图片引用。
- 预处理缩略图引用。
- OCR 或视觉解析文本。
- 关键区域裁剪信息。

### 7.2 关键帧记录

实时阶段建议额外存储：

- `frame_id`
- `session_id`
- `timestamp`
- `trigger_reason`
- `clarity_score`
- `selected_for_reasoning`

## 8. 长期记忆与向量扩展

后续阶段可引入向量记忆，记录以下语义特征：

- 高频错因模式。
- 稳定薄弱模块。
- 常用有效隐喻。
- 易触发挫败感的题型。

引入原则：

- 只保存高价值、可复用的学习特征。
- 不保存冗余逐字对话。

## 9. 数据保留与隐私

- 默认仅保存必要的学习数据。
- 原始音视频流不做无限期保留。
- 报告类数据优先保存摘要而非完整内容。
- 删除学生时，应支持成组删除相关记录。

## 10. 建议数据库表

- `students`
- `strategy_profiles`
- `problems`
- `sessions`
- `turns`
- `diagnoses`
- `practices`
- `reports`
- `artifacts`

## 11. 一致性约束

- 一个 `problem` 可以关联多个 `session`。
- 一个 `session` 必须属于一个 `student`。
- 一个 `diagnosis` 必须绑定具体 `problem` 和 `session`。
- 一个 `practice` 必须能追溯到来源题。

## 12. 数据层测试重点

- 会话恢复是否可靠。
- 摘要是否能复原关键状态。
- 错题本查询是否正确聚合。
- 删除与更新是否保持引用一致。
- 实时阶段关键帧是否能与推理结果正确关联。
