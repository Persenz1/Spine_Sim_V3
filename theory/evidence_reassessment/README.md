# 论文反向证据复核输入

**状态：** non-normative evidence input
**用途：** 后续从论文稿、形式化推导和 accepted 模型反向检查工程事实与文献证据，识别可补充、需修订或证据不足的内容。

本目录把反向复核所需的工程事实汇总和 29 组文献提取材料以工作副本形式集中放在 `theory/` 下，便于与论文、模块模型、接口合同和复核报告逐项对照。归档中的源文件仍完整保留。这里的材料不是当前理论正文，也不会自动覆盖 accepted 1.0。

## 目录

```text
evidence_reassessment/
├── README.md
├── engineering_fixed_context.md
└── literature/
    ├── 01_frictional_engagement/
    ├── ...
    └── 29_wheeled_wall_climbing_robot/
```

每个文献目录保留：

- `evidence_card.md`：与本项目机理相关的证据卡；
- `extraction_audit.json`：提取过程和完整性审计；
- `figures/`：从原文筛出的关键图片（若该文献有图片）。

## 本轮反向审查输出（2026-07-17）

- [`reverse_audit_2026-07-17/MECHANISM_EVIDENCE_REASSESSMENT_REPORT.md`](reverse_audit_2026-07-17/MECHANISM_EVIDENCE_REASSESSMENT_REPORT.md)：29 组文献卡对 `FORMAL 0.1.0-proposed`、accepted A/B/C/System 与独立复核边界的总审查；
- [`reverse_audit_2026-07-17/REVIEW_PROTOCOL.md`](reverse_audit_2026-07-17/REVIEW_PROTOCOL.md)：统一分类、适用域和报告要求；
- [`reverse_audit_2026-07-17/individual/`](reverse_audit_2026-07-17/individual/)：29 份逐卡独立报告。

上述输出均为 non-normative review material，不直接修改 accepted 1.0，也不把文献公式或数值提升为项目参数。

归档的每个文献目录继续完整保留 `.zip`、`evidence_card.md`、`extraction_audit.json` 和 `figures/`。本目录只复制非 ZIP 材料，避免把原始压缩包加入理论工作区。

## 权威边界

1. `engineering_fixed_context.md` 是归档中工程事实 1.0.0 生成视图的字节级副本；归档同时保留该生成视图及其结构化 YAML 源、schema、manifest 和生成器。
2. 文献证据卡、审计 JSON 和图片用于查证来源、适用域和可补充机理，不是新的固定参数或已接受模型。
3. 反向复核发现的新内容必须先形成明确的 proposed 补充或版本化修订，再经过审查进入 accepted 模型；不得直接拼入现行规范。
4. 需要核对源字节、重跑生成器或复现实验时，应回到归档中的完整提取目录、内部事实源和运行 manifest；理论工作副本不得反向覆盖归档。

## 建议的后续反向复核顺序

1. 以论文稿或 accepted 模型的一节为检查对象；
2. 对照工程事实，检查几何、坐标、工况、开关和未决参数；
3. 按文献路由读取对应证据卡及关键图片；
4. 把结论分为 `supported / supplement_candidate / conflict / insufficient_evidence`；
5. 对补充候选建立来源、适用条件、影响模块和验证义务；
6. 单独提出 proposed 修订，不直接改写 accepted 文件。
