# 网页端 Pro 机理推导归档

> 归档日期：2026-07-17
> 原布局最后提交：`891d14c`（`Accept system integrated model`）
> 状态：只读审计与复现材料；当前理论入口已经迁移到仓库根目录 `theory/`

## 1. 归档边界

本目录保存网页端 Pro 机理推导的完整工程链，包括工作流规则、工程事实、文献证据、正式提示词、原始回答、下载原件、候选稿、机械修复、验证脚本、验证报告和阶段快照。

归档文件中出现的 `docs/...`、`engineering_fixed_context/...` 和 `derivation/...` 路径是运行当时的历史路径，应保留用于输入哈希和审计。需要在原路径下逐字复现实验时，应在独立 worktree 中检出提交 `891d14c`，不要批量改写归档清单。

当前有效正式理论文件及理论工作副本的位置：

| 归档/原位置 | 当前使用位置 | 关系 |
|---|---|---|
| `derivation/system/SYSTEM_INTEGRATED_MODEL.md` | `theory/system/SYSTEM_INTEGRATED_MODEL.md` | accepted 正式文件已迁出归档 |
| `derivation/modules/*/final/*_INTEGRATED_MODEL.md` | `theory/modules/` | accepted 正式文件已迁出归档 |
| `derivation/contracts/*.md` | `theory/interfaces/` | accepted 独立合同已迁出归档 |
| `derivation/modules/*/current/*_MODULE_CONTEXT.md` | `derivation/modules/*/history/*_after_A3/B3/C3.md` | 最终上下文只作历史快照，不再保留 theory 重复副本 |
| `engineering_fixed_context/engineering_fixed_context.md` | `theory/evidence_reassessment/engineering_fixed_context.md` | 归档源保留，theory 为字节级工作副本 |
| `docs/extract/机理提取/*/{evidence_card.md,extraction_audit.json,figures/}` | `theory/evidence_reassessment/literature/` | 归档源保留，theory 为非 ZIP 工作副本 |

## 2. 目录与职责

```text
web_pro_derivation_2026-07-17/
├── README.md
├── docs/
│   ├── derivation_workflow/
│   │   ├── DERIVATION_WORKFLOW.md
│   │   ├── guides/                 # 提示词编写与运行产物处理规范
│   │   ├── templates/              # 四类子模块输出合同
│   │   └── window_prompts/         # 单任务 Codex 窗口入口
│   └── extract/
│       ├── ENGINEERING_FIXED_CONTEXT.md
│       ├── MECHANISM_MODULE_PLAN.md
│       ├── LITERATURE_MODULE_ROUTING.md
│       └── 机理提取/               # 29 组 ZIP、证据卡、审计 JSON 和图片完整源
├── engineering_fixed_context/
│   ├── engineering_fixed_context.md
│   └── internal/                   # YAML 事实源、manifest、schema、生成器、变更记录
└── derivation/
    ├── prompts/                    # A1–C3、A/B/C 集成、系统集成提示词
    ├── runs/                       # 13 个不可覆盖的运行归档
    └── modules/*/history/          # 九个子模块的阶段完整上下文快照
```

## 3. 每类运行产物的意义

| 文件或目录 | 生命周期与意义 | 后续默认使用 |
|---|---|---|
| `derivation/prompts/*` | 执行前定稿的正式网页提示词；规定对象、范围、输入、证据、输出和完成判据 | 否；只在审计任务边界时读取 |
| `runs/<TASK>/PROMPT.md` | 本轮实际执行提示词的冻结副本，不随后来提示词修改 | 否 |
| `INPUT_MANIFEST.yaml` | 记录 run_id、实际运行目录、输入 Git 提交、文件版本、字节数和 SHA-256 | 复现时使用 |
| `RAW_RESPONSE.md` | 网页端完整原始回答，永不回写修复 | 原文审计时使用 |
| `raw_downloads/` | 浏览器下载原件，保留重名后缀和原始字节 | 原件对照时使用 |
| `MODULE_CONTEXT_CANDIDATE.md` | 从网页产物拆出的完整滚动上下文候选 | 已被 accepted 当前版和集成模型取代 |
| `*_INTEGRATED_MODEL_CANDIDATE.md` | A/B/C 或系统集成候选 | 已被 `theory/` 正式 accepted 文件取代 |
| `*_CONTRACT_CANDIDATE.md` | 层间合同候选 | 已被 `theory/interfaces/` 取代 |
| `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` | Pro 给出的完整工程事实候选视图，不能直接覆盖正式事实源 | 仅用于当轮 diff；九轮均无正式变化 |
| `RUN_UPDATE_SUMMARY_CANDIDATE.yaml` | 网页下载的原始结构化变化摘要候选 | 审计候选修复时使用 |
| `RUN_UPDATE_SUMMARY.yaml` | 修复并验证后的子模块变化摘要 | 本地审计；不进入下一轮网页上下文 |
| `CITATION_BRIEF.md` | 单轮关键公式、方法和来源的简短旁路说明 | 仅最终论文引用整理时按需读取 |
| `MECHANICAL_FIXES.md` | 格式、路径、元数据、状态或无歧义数学修复记录 | 追查接受版与原件差异时使用 |
| `VALIDATION_REPORT.md` | 输入、语义、合同、回归、Markdown、工程事实和接受状态的最终检查报告 | 判断产物是否已接受时使用 |
| `validate_inputs.py` | 冻结输入、哈希、压缩包和前置状态复验 | 复现验证时使用 |
| `validate_artifacts.py` | 产物结构、公式构造、事件/事务、合同一致性等回归检查 | 复现验证时使用 |
| `modules/*/history/` | 每个 A1–C3 阶段结束时的完整 accepted 上下文快照 | 只做阶段差异和返工追溯 |

## 4. 运行目录与主结果

| 运行 | 主结果 | 当前正式去向 |
|---|---|---|
| `A1`、`A2`、`A3` | 逐步滚动的完整 A 上下文 | `derivation/modules/A/history/A_MODULE_CONTEXT_after_A3.md`；正式层内规范为 A 集成模型 |
| `A_INTEGRATION` | A 集成模型、A→B 合同 | `theory/modules/A_INTEGRATED_MODEL.md`、`theory/interfaces/A_TO_B_CONTRACT.md` |
| `B1`、`B2`、`B3` | 逐步滚动的完整 B 上下文 | `derivation/modules/B/history/B_MODULE_CONTEXT_after_B3.md`；正式层内规范为 B 集成模型 |
| `B_INTEGRATION` | B 集成模型、B→C 合同 | `theory/modules/B_INTEGRATED_MODEL.md`、`theory/interfaces/B_TO_C_CONTRACT.md` |
| `C1`、`C2`、`C3` | 逐步滚动的完整 C 上下文 | `derivation/modules/C/history/C_MODULE_CONTEXT_after_C3.md`；正式层内规范为 C 集成模型 |
| `C_INTEGRATION` | C 集成模型 | `theory/modules/C_INTEGRATED_MODEL.md` |
| `SYSTEM_INTEGRATION` | A/B/C 全局集成模型 | `theory/system/SYSTEM_INTEGRATED_MODEL.md` |

## 5. 验证与变更摘要

- 13 个运行目录均包含 `RAW_RESPONSE.md` 和 `VALIDATION_REPORT.md`。
- A1–C3、A/B/C 集成和 SYSTEM 集成的正式结果均为 `pass` 或 `pass / accepted`。
- 九个子模块的 `RUN_UPDATE_SUMMARY.yaml` 均记录 `engineering_context_delta.operation: none`；工程事实保持 `1.0.0`，没有接受新的固定数值、扫描集合、坐标、边界、模型开关或范围。
- A、B、C 和系统集成结果均为 `1.0.0 accepted`，但只认证理论与接口规范；代码、参数、数值和实验仍未认证。
- 系统验证明确保留 B→C 运动合同缺口：B 1.0 不支持正式非零偏心路径需要的局部 y、动态姿态和完整 twist。

## 6. 归档使用原则

1. 普通理论复核不要读取本目录；先从 `theory/README.md` 和系统模型开始。
2. 不把候选稿、原始回答或阶段快照当作当前规范。
3. 不把 `CITATION_BRIEF` 合并回模块上下文；它只在最终论文引用整理时提供线索。
4. 不修改历史 manifest 中的原始路径和哈希；路径变化通过本 README 的迁移表解释。
5. 若理论复核发现实质问题，在 `theory/` 创建清晰的修订或论文稿，不直接改写原始网页归档。
