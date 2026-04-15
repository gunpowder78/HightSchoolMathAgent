from __future__ import annotations

class RepairService:
    """Repair protocol library for common cognitive bugs."""

    _PROTOCOLS: dict[str, dict[str, object]] = {
        "整体换元": {
            "protocol_id": "RP-BUG-01",
            "name": "整体换元熔断修复",
            "steps": [
                "先暂停推进新内容，分离变量范围计算和图像判定",
                "先求大写变量范围，再在单位圆切片定界",
                "复做一题同构题并口头解释每一步",
            ],
            "expected_outcome": "从代数混乱回到可视化定界流程",
        },
        "立体建系": {
            "protocol_id": "RP-BUG-02",
            "name": "立体建系熔断修复",
            "steps": [
                "使用实体模型重建墙角与垂线直觉",
                "固定原点与三轴后再回到纸面坐标",
                "仅训练第一问建系动作直到稳定",
            ],
            "expected_outcome": "重建空间坐标机械化流程",
        },
    }

    def get_protocol(self, target_node: str) -> dict[str, object]:
        key = target_node.strip()
        protocol = self._PROTOCOLS.get(key)
        if protocol is None:
            protocol = {
                "protocol_id": "RP-GENERIC",
                "name": "通用熔断修复",
                "steps": [
                    "暂停新增内容 1 天",
                    "回到白名单基础题",
                    "进行三题切片复评后再恢复推进",
                ],
                "expected_outcome": "恢复掌控感并降低认知负荷",
            }
        return protocol

    @staticmethod
    def serialize(protocol: dict[str, object]) -> dict[str, object]:
        return dict(protocol)
