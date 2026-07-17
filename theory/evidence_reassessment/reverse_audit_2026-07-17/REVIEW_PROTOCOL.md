# 29 组原始文献卡对现行完整机理的反向审查协议

**状态：** non-normative review working material
**审查日期：** 2026-07-17
**目的：** 逐卡识别现行机理对原始文献结论的支持、冲突、遗漏与可补充内容；本目录不修改 accepted 1.0，也不把文献经验值自动提升为项目参数。

## 审查对象

每个独立审查必须同时考虑：

1. 对应 `literature/<NN_...>/evidence_card.md`、`extraction_audit.json` 与必要的关键图片；
2. `paper/MECHANISM_DERIVATION_FORMAL.md`（`0.1.0-proposed`，本轮“完整机理”主审对象）；
3. `system/SYSTEM_INTEGRATED_MODEL.md` 与相关 A/B/C accepted 集成模型（现行规范基线）；
4. `review/DERIVATION_VERIFICATION_2026-07-17.md`（已知 P0/P1 与建议闭合边界）；
5. 必要时查询 `engineering_fixed_context.md`，但不得用文献覆盖固定工程事实。

## 分类

- `supported`：机理已经包含该结论，且适用域与文献不发生实质冲突；
- `supplement_candidate`：文献有项目相关结论，而现行机理缺失或仅隐含；只能形成 proposed 补充候选；
- `conflict`：在相同对象、假设和适用域下，现行机理与文献结论不兼容；必须区分真正冲突与模型范围差异；
- `insufficient_evidence`：证据卡、提取审计或原文适用域不足以支持移植。

## 每份独立报告的最低内容

1. 文献卡身份、提取完整性和适用域；
2. 逐项结论表：卡片原结论、本地来源行号/图片、机理对应位置与行号、分类、理由；
3. 真冲突与表面冲突；
4. 被漏掉的关键结论；
5. 可补充项：建议进入的层级/章节、建议身份（假设、可选模型、验证义务、输出字段、参数先验等）、适用条件与验证义务；
6. 明确列出不可直接移植的参数或结论；
7. 按 P0/P1/P2/P3 给出优先级和置信度。

所有引用应指向仓库内文件并给出 1-based 行号。结论必须区分“文献支持某种现象/建模方向”和“文献足以支持本项目采用某个公式或数值”。
