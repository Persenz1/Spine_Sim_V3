# 机理推导文档架构与网页端工作流

> 版本：`1.0.0`
>
> 用途：规定 A1–C3 机理推导过程中需要维护、滚动、冻结和归档的文件，以及每类网页端 Pro 任务应上传哪些输入、输出哪些结果。
>
> 边界：本文件管理推导工程，不定义具体接触、摩擦、损伤或载荷重分配机理。

## 1. 总体原则

1. 工程事实与机理实现分离。坐标、尺寸、参数范围、工况和接口能力进入 `engineering_fixed_context`；方程、状态机和算法进入 `MODULE_CONTEXT` 或 `INTEGRATED_MODEL`。
2. 每个大模块只维护一份当前滚动上下文，不同时维护内容重复的 `A1_RESULT` 和 `A_MODULE_CONTEXT`。
3. A1/A2/A3 等阶段结果通过版本快照留档，不作为后续网页任务的默认上传文件。
4. 每个大模块的三个子模块完成后必须进行一次独立集成，不能把顺序完成三个子模块直接视为大模块完成。
5. A、B、C 全部集成后必须进行一次全局一致性审查。
6. 备用文献和历史文件按需上传，不默认占用 Pro 上下文。
7. Pro 可以提出工程事实变更，但不能自动将机理结论提升为正式工程事实。
8. 人工保留最终控制权；关键工程事实变化必须经过语义说明、差异审查和人工确认。

## 2. 文件类型及职责

| 文件 | 职责 | 生命周期 | 网页端使用 |
|---|---|---|---|
| `engineering_fixed_context.md` | 当前完整工程事实、边界、工况、开关和未决参数 | 全工程滚动更新 | 每轮使用最新正式版 |
| `A1_PROMPT.md` 等 | 当前子模块的系统化执行提示词 | 执行前定稿，之后冻结 | 当前子模块必传 |
| `A_MODULE_CONTEXT.md` | A 模块当前已经接受的完整机理上下文 | A1→A2→A3 滚动 | A2、A3 和 A 集成使用 |
| `B_MODULE_CONTEXT.md` | B 模块当前已经接受的完整机理上下文 | B1→B2→B3 滚动 | B2、B3 和 B 集成使用 |
| `C_MODULE_CONTEXT.md` | C 模块当前已经接受的完整机理上下文 | C1→C2→C3 滚动 | C2、C3 和 C 集成使用 |
| `A_INTEGRATED_MODEL.md` | A1–A3 一致性集成后的正式 A 模型 | A 集成后冻结 | B 层审计和最终系统集成 |
| `B_INTEGRATED_MODEL.md` | B1–B3 一致性集成后的正式 B 模型 | B 集成后冻结 | C 层审计和最终系统集成 |
| `C_INTEGRATED_MODEL.md` | C1–C3 一致性集成后的正式 C 模型 | C 集成后冻结 | 最终系统集成 |
| `A_TO_B_CONTRACT.md` | A 向 B 暴露的稳定接口 | A 集成后冻结 | B1–B3 的上游输入 |
| `B_TO_C_CONTRACT.md` | B 向 C 暴露的稳定接口 | B 集成后冻结 | C1–C3 的上游输入 |
| 阶段快照 | 保存每轮结束时的完整 `MODULE_CONTEXT` | 永久归档 | 默认不上传 |
| 原始 Pro 回答 | 保留网页原始输出和证据上下文 | 永久归档 | 仅在审计或返工时使用 |
| 输入清单 | 记录提示词、工程事实版本和文献包 | 每次运行归档 | 用于复现，不默认上传 |

## 3. 建议的本地目录结构

以下结构在正式开始 A1 时建立；当前文件只规定结构，不提前创建空目录。

```text
derivation/
├── prompts/
│   ├── A/
│   │   ├── A1_PROMPT.md
│   │   ├── A2_PROMPT.md
│   │   ├── A3_PROMPT.md
│   │   └── A_INTEGRATION_PROMPT.md
│   ├── B/
│   ├── C/
│   └── SYSTEM_INTEGRATION_PROMPT.md
├── modules/
│   ├── A/
│   │   ├── current/
│   │   │   └── A_MODULE_CONTEXT.md
│   │   ├── history/
│   │   │   ├── A_MODULE_CONTEXT_after_A1.md
│   │   │   ├── A_MODULE_CONTEXT_after_A2.md
│   │   │   └── A_MODULE_CONTEXT_after_A3.md
│   │   └── final/
│   │       └── A_INTEGRATED_MODEL.md
│   ├── B/
│   └── C/
├── contracts/
│   ├── A_TO_B_CONTRACT.md
│   └── B_TO_C_CONTRACT.md
├── runs/
│   ├── A1/
│   │   ├── PROMPT.md
│   │   ├── INPUT_MANIFEST.yaml
│   │   ├── RAW_RESPONSE.md
│   │   └── RUN_UPDATE_SUMMARY.md
│   └── ...
└── system/
    └── SYSTEM_INTEGRATED_MODEL.md
```

## 4. 提示词生成流程

每个子模块的提示词单独生成、单独审查，不用一个通用提示词替代全部九个模块。

### 4.1 生成提示词草稿时上传

1. 最新正式版 `engineering_fixed_context/engineering_fixed_context.md`；
2. `docs/extract/MECHANISM_MODULE_PLAN.md`；
3. `docs/extract/LITERATURE_MODULE_ROUTING.md`。

该任务只生成目标子模块的提示词草稿，不执行机理推导。

### 4.2 提示词本地定稿

草稿保存后，由 Codex按结构化工程要求检查并补充：

- 模块编号、提示词版本和输入版本；
- 本轮明确范围及不处理内容；
- 必须回答的问题和完成判据；
- 最小文献包及各文献使用边界；
- 禁止硬编码和禁止越层定义的内容；
- 输出文件和语义变更说明格式；
- 与上游合同和当前模块上下文的关系；
- 验证、自检和未决问题要求。

提示词可以提前生成骨架，但必须在执行前根据最新工程事实、上游合同和模块上下文重新校准。

## 5. 子模块网页任务的上传规则

### 5.1 A1

默认上传：

1. 最新 `engineering_fixed_context.md`；
2. `A1_PROMPT.md`；
3. A1 最小文献包。

A1 尚无既有 `A_MODULE_CONTEXT`。A1 完成时生成的完整 `A_MODULE_CONTEXT.md` 就是 A1 的正式阶段结果，不再创建内容重复的 `A1_RESULT.md`。

### 5.2 A2 和 A3

默认上传：

1. 最新 `engineering_fixed_context.md`；
2. 当前子模块提示词；
3. 最新完整 `A_MODULE_CONTEXT.md`；
4. 当前子模块最小文献包。

A2 输出融合 A1+A2 的完整 `A_MODULE_CONTEXT`；A3 输出融合 A1+A2+A3 的完整 `A_MODULE_CONTEXT`。不得只输出本轮增量而丢失此前已接受内容。

### 5.3 B1、B2、B3

B1 默认上传最新工程事实、`B1_PROMPT`、`A_TO_B_CONTRACT` 和 B1 最小文献包。B2、B3 在此基础上增加最新完整 `B_MODULE_CONTEXT`。

除非需要审计 A 层具体推导，B 层不默认上传完整 `A_INTEGRATED_MODEL` 或 A1–A3 历史快照。

### 5.4 C1、C2、C3

C1 默认上传最新工程事实、`C1_PROMPT`、`B_TO_C_CONTRACT` 和 C1 最小文献包。C2、C3 在此基础上增加最新完整 `C_MODULE_CONTEXT`。

除非需要审计 B 层具体推导，C 层不默认上传完整 B1–B3 历史快照。

## 6. 每个子模块的输出协议

每次 Pro 推导至少输出以下内容：

### 6.1 `MODULE_CONTEXT`

输出当前大模块的最新完整版本，内容至少包括：

- 范围和明确不处理的内容；
- 状态变量与历史变量；
- 坐标、符号和单位；
- 平衡方程及约束；
- 状态转换和事件；
- 输入/输出接口；
- 参数来源和状态；
- 文献证据及适用边界；
- 尚未解决的问题；
- 对后续子模块的交接要求。

### 6.2 最新完整工程事实候选

按当前正式版内容输出最新完整 `engineering_fixed_context.md` 候选。机理方程、状态机和算法不得写入该文件。

### 6.3 `RUN_UPDATE_SUMMARY`

该说明不需要成为长期滚动文件，但必须随原始运行记录归档，至少包括：

```yaml
engineering_context_delta:
  - id: 事实编号或 none
    operation: add | modify | deprecate | none
    reason: 为什么建议变化
    affected_modules: []
    evidence: 对应推导或文献位置

module_context_delta:
  - 本轮新增、修改或仍未解决的关键内容
```

Pro 不需要为每个输出文件编写独立 Changelog。Codex根据语义说明和实际 diff 维护正式变更记录。

## 7. 阶段快照和本地归档

每轮完成后由 Codex执行：

1. 保存执行提示词；
2. 保存输入文件及版本清单；
3. 保存 Pro 原始回答；
4. 检查工程事实候选与当前正式版的差异；
5. 检查机理内容是否错误进入工程事实；
6. 保存本轮结束后的完整 `MODULE_CONTEXT` 快照；
7. 将通过审查的版本更新为 `current/MODULE_CONTEXT.md`；
8. 将关键工程事实变化提交人工确认。

阶段快照用于追溯和返工，不默认上传给下一子模块。相邻快照的 diff 用于判断 A2、A3 等阶段分别改变了什么。

## 8. 大模块集成

三个子模块按顺序完成后，必须新开 Pro 任务执行大模块集成。

### 8.1 默认上传三个文件

以 A 模块为例：

1. 最新正式 `engineering_fixed_context.md`；
2. 最新完整 `A_MODULE_CONTEXT.md`，其中已包含 A1+A2+A3；
3. `A_INTEGRATION_PROMPT.md`。

默认不上传 A1/A2/A3 阶段快照，也不重新上传原始论文。若集成发现信息丢失、证据冲突或模型假设不成立，再补充目标快照或对应文献包。

### 8.2 集成任务

集成不是简单拼接，必须检查：

- 状态变量能否组成完整状态系统；
- 上一子模块的输出是否足够支持下一子模块；
- 坐标、符号、单位、力和功方向是否一致；
- 同一柔顺或失效是否被重复计入；
- 事件冲突和优先级是否明确；
- 是否能够形成可执行的单步算法；
- 哪些内容对下游公开，哪些保持模块内部；
- 未决问题是否被保留而非静默消失。

A、B 集成分别输出 `A_TO_B_CONTRACT`、`B_TO_C_CONTRACT`。合同内容同时嵌入对应 `INTEGRATED_MODEL` 的接口章节，便于最终全局集成时减少上传文件数。

## 9. A/B/C 全局集成

A、B、C 三个大模块全部完成后，新开 Pro 任务，默认上传五个文件：

1. 最新正式 `engineering_fixed_context.md`；
2. `A_INTEGRATED_MODEL.md`；
3. `B_INTEGRATED_MODEL.md`；
4. `C_INTEGRATED_MODEL.md`；
5. `SYSTEM_INTEGRATION_PROMPT.md`。

`A_TO_B_CONTRACT` 和 `B_TO_C_CONTRACT` 已嵌入对应集成模型，因此不额外占用上传文件。原始论文和子模块快照同样不默认上传。

全局集成重点检查：

- A→B→C 变量和状态是否闭合；
- 坐标变换、符号、单位和功方向是否全局一致；
- 高层是否越权重定义低层机理；
- 工程事实是否被完整遵守；
- 各层终止条件是否互相兼容；
- 是否保留实验验证所需的原始输出和事件历史。

## 10. 工程事实变更审批

工程事实正式更新流程：

```text
Pro 输出完整候选和语义变化说明
  → Codex 检查候选与正式版 diff
  → Codex 区分工程事实、机理实现和不充分推断
  → 向人工报告建议接受、建议拒绝和需要决定的事项
  → 人工确认关键变化
  → 更新 engineering_fixed_context/internal/facts/*.yaml
  → 重新生成并校验 engineering_fixed_context.md
```

只看文本 diff 不足以判断变化是否合理，因此 Pro 必须说明变更理由；但正式 Changelog、版本快照和结构化合并由 Codex负责。

## 11. 默认不上传的内容

除非出现明确审计需要，以下内容只做本地存档：

- 历史提示词和提示词草稿；
- 旧版 `MODULE_CONTEXT`；
- Pro 原始回答；
- 输入清单和文本 diff；
- 被否决的模型和临时计算；
- 备用文献包；
- 已经被下游合同压缩的上游完整推导。

该规则的目的不是删除信息，而是避免无关历史占用当前 Pro 任务的上下文。
