# HightSchoolMathAgent

面向广东新高考艺术生的本地数学辅导 Agent。

当前仓库已包含：

- `doc/sdd-tdd/`
  - 完整的需求、规划、设计、开发、测试文档基线。
- `app/`
  - M1 本地 MVP 的代码骨架。
- `prompts/`
  - 提示词模板占位目录。
- `tests/`
  - 基础单元测试与集成测试骨架。

## 当前 M1 骨架能力

- 本地 `Gradio` 页面。
- 文本题目输入和图片占位接入。
- `FakeTutorModelAdapter` 驱动的最小可运行辅导流程。
- `SQLite + WAL` 本地会话存储。
- 基础测试样例。

## 快速开始

1. 创建虚拟环境并安装依赖

```bash
pip install -r requirements.txt
```

2. 启动本地 MVP

```bash
python -m app.main
```

3. 运行测试

```bash
pytest
```

## 下一步建议

- 用真实模型适配器替换 `FakeTutorModelAdapter`
- 接入图片 OCR / 视觉解析
- 实现错题本查询与周报生成
- 补齐 `FR-01` 到 `FR-15` 的完整实现
