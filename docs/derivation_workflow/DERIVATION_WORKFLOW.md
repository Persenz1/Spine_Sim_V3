# 机理推导文档架构与网页端工作流

> 版本：`1.3.2`
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
9. 最小文献包是优先证据集，不是封闭知识集。上传论文无法覆盖完整机理时，Pro 可在明确标注来源和适用边界的前提下，使用自身通用知识、互联网公开资料和公开数据库；A1 的地形生成机理尤其鼓励这样补足。
10. 每轮额外输出一份简短论文式 `CITATION_BRIEF.md`。该文件只做本地归档，不进入后续子模块、模块集成、工程事实审批或其他默认交互；仅在完整机理形成后且人工明确要求时再做汇总整理。
11. YAML 整理、模板适配、文件命名、路径修复、diff、版本核对、生成器校验和本地归档属于 Codex 的机械职责，不要求人工参与。只有工程事实是否接受、物理机理如何取舍、范围是否改变等语义决定才提交人工确认。

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
| `RUN_UPDATE_SUMMARY.yaml` | 本轮工程事实候选变化、模块变化和输出自检 | 每次运行永久归档 | 用于 Codex 本地审查；不默认上传 |
| `CITATION_BRIEF.md` | 本轮关键公式和结论的简短论文式引文说明 | 每次运行永久归档；不滚动 | 不上传；仅在人工明确要求最终汇总时使用 |
| 阶段快照 | 保存每轮结束时的完整 `MODULE_CONTEXT` | 永久归档 | 默认不上传 |
| 原始 Pro 回答 | 保留网页原始输出和证据上下文 | 永久归档 | 仅在审计或返工时使用 |
| 输入清单 | 记录提示词、工程事实版本和文献包 | 每次运行归档 | 用于复现，不默认上传 |

## 3. 建议的本地目录结构

规范模板和指导固定保存在 `docs/derivation_workflow/`，不复制到运行产物目录：

```text
docs/derivation_workflow/
├── DERIVATION_WORKFLOW.md
├── templates/
│   ├── MODULE_CONTEXT_TEMPLATE.md
│   ├── ENGINEERING_FIXED_CONTEXT_CANDIDATE_TEMPLATE.md
│   ├── RUN_UPDATE_SUMMARY_TEMPLATE.yaml
│   └── CITATION_BRIEF_TEMPLATE.md
└── guides/
    ├── PROMPT_AUTHORING_GUIDE.md
    └── RUN_ARTIFACT_HANDLING_GUIDE.md
```

`derivation/` 只保存正式提示词、推导结果和运行归档。以下结构在正式开始 A1 时按需建立，不提前创建无内容文件：

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
│   │   ├── MODULE_CONTEXT_CANDIDATE.md
│   │   ├── ENGINEERING_FIXED_CONTEXT_CANDIDATE.md
│   │   ├── CITATION_BRIEF.md
│   │   └── RUN_UPDATE_SUMMARY.yaml
│   └── ...
└── system/
    └── SYSTEM_INTEGRATED_MODEL.md
```

## 4. 提示词生成流程

每个子模块的提示词单独生成、单独审查，不用一个通用提示词替代全部九个模块。

所有提示词的编写遵循 `docs/derivation_workflow/guides/PROMPT_AUTHORING_GUIDE.md`。该指导只规定编写前必须阅读的输入和提示词必须覆盖的内容，不强制所有任务采用同一排版模板。

### 4.1 生成提示词草稿时上传

1. 最新正式版 `engineering_fixed_context/engineering_fixed_context.md`；
2. `docs/extract/MECHANISM_MODULE_PLAN.md`；
3. `docs/extract/LITERATURE_MODULE_ROUTING.md`。

该任务只生成目标子模块的提示词草稿，不执行机理推导。

### 4.2 提示词本地定稿

草稿保存后，由 Codex按结构化工程要求检查并补充：

- 模块编号、提示词版本和输入版本；
- 研究对象、工程背景、完整物理链以及当前任务在系统中的位置；
- 本轮明确范围及不处理内容；
- 必须回答的问题和完成判据；
- 最小文献包及各文献使用边界；
- 禁止硬编码和禁止越层定义的内容；
- 输出文件和语义变更说明格式；
- 与上游合同和当前模块上下文的关系；
- 验证、自检和未决问题要求。
- 外部知识、网络公开资料、公开数据库和本地文献的来源标注要求；
- 仅本地归档的 `CITATION_BRIEF.md` 输出要求。

输入文件必须在提示词正文中逐项列出，并说明每个文件的作用、优先级和是否要求完整阅读；不得只依赖另附的 `INPUT_MANIFEST.yaml` 让 Pro 猜测输入关系。

提示词可以提前生成骨架，但必须在执行前根据最新工程事实、上游合同和模块上下文重新校准。

### 4.3 自身知识、网络资料和公开数据库的使用规则

最小上传文献优先用于确定直接证据、模型边界和已知冲突，但不得因上传论文覆盖不足而强行把机理留空或把单篇论文外推成普适定律。必要时允许 Pro：

- 使用自身已有的通用数学、数值方法、接触几何、随机场和表面形貌知识；
- 检索互联网公开资料；
- 查询政府、科研机构、标准组织、仪器厂商或其他可追溯公开数据库；
- 将外部数据用于提出参数先验、候选范围、生成方法或验证方法。

使用时必须遵守：

1. 最新正式 `engineering_fixed_context.md` 始终高于外部资料和自身知识；不得静默改写已固定事实。
2. 外部数值、数据集和材料专属结论必须给出可直接访问的来源网址，并在正文说明对象、尺度、单位、版本或访问条件以及能否迁移到本项目。
3. 自身知识只能作为明确标注的通用知识或推导起点，必须说明假设、适用条件和不确定性；不得伪造论文、数据库或网址。
4. 无法证明材料专属性时，应输出参数化模型、候选范围或待标定项，不得把通用粗糙表面模型硬写成红砖、混凝土或某目数砂纸的唯一统计规律。
5. 外部来源提出的工程事实变化仍须进入候选变更和人工审批流程，不能因有网址而自动升级为正式工程事实。
6. 优先引用原始论文、官方数据库、标准或机构页面；搜索结果页、无来源转载和无法复核的汇总值不能作为关键参数的唯一依据。
7. 所有实际使用的来源同时进入本轮 `CITATION_BRIEF.md`；该文件仅供本地追溯，不加入任何默认上传链。

## 5. 子模块网页任务的上传规则

### 5.1 A1

默认上传：

1. 最新 `engineering_fixed_context.md`；
2. `docs/extract/MECHANISM_MODULE_PLAN.md`；
3. `A1_PROMPT.md`；
4. `MODULE_CONTEXT_TEMPLATE.md`；
5. `ENGINEERING_FIXED_CONTEXT_CANDIDATE_TEMPLATE.md`；
6. `RUN_UPDATE_SUMMARY_TEMPLATE.yaml`；
7. `CITATION_BRIEF_TEMPLATE.md`；
8. A1 最小文献包。

A1 尚无既有 `A_MODULE_CONTEXT`。A1 完成时生成的完整 `A_MODULE_CONTEXT.md` 就是 A1 的正式阶段结果，不再创建内容重复的 `A1_RESULT.md`。

`CITATION_BRIEF.md` 不属于 A1 的默认上传输入，也不在 A2 中回传。

`LITERATURE_MODULE_ROUTING.md`、`DERIVATION_WORKFLOW.md`、提示词编写指导和本地运行产物处理指导是 Codex 的编写/管理依据，不默认上传给执行 A1 的 Pro；与 A1 有关的文献角色、工作流要求和输出规则必须已经写入 `A1_PROMPT.md`，避免全量管理文档占用推理上下文。

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

每次 Pro 推导至少输出以下四类内容。具体格式遵循 `docs/derivation_workflow/templates/`；模板规定输出结构，不改变各文件的上传生命周期。

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

候选必须严格遵守 `engineering_fixed_context/internal/` 的单向维护和生成约束：

- 候选只是人工审阅视图，正式源始终是 `internal/facts/*.yaml`；不得直接把候选覆盖到正式生成文件。
- 候选正文必须保持 `build_context.py` 的渲染结构，不添加 `candidate-from-*` 文件头、变更附录或 schema 之外的字段。
- 若无工程事实变化，候选应与输入正式版逐字一致。
- 若有变化，`RUN_UPDATE_SUMMARY.yaml` 必须同时给出能映射回 `schema.yaml` 的完整 `proposed_fact`；只给自然语言差异不合格。
- 修改既有基线事实时保留其原始 `id`、`order` 和 `provenance`，避免破坏 `manifest.yaml` 的基线章节覆盖校验；新增证据另记在运行摘要。
- 新增事实的 `provenance.source` 必须是仓库内实际存在的本地相对路径，不能直接填写网址；外部网址放入运行摘要的证据字段。
- 正式接受变化后，Codex 修改 YAML，依次执行 `--write` 和 `--check`，不得反向手改生成后的 Markdown。

### 6.3 `RUN_UPDATE_SUMMARY`

该说明不需要成为长期滚动文件，但必须随原始运行记录归档，至少包括：

```yaml
engineering_context_delta:
  - id: 事实编号或 none
    operation: add | modify | none
    reason: 为什么建议变化
    affected_modules: []
    evidence: 对应推导或文献位置

module_context_delta:
  - 本轮新增、修改或仍未解决的关键内容
```

Pro 不需要为每个输出文件编写独立 Changelog。Codex根据语义说明和实际 diff 维护正式变更记录。

### 6.4 `CITATION_BRIEF`

额外输出一份简短、可独立阅读的论文式引文说明，只摘录本轮最关键的公式、方法选择和结论，不复制完整 `MODULE_CONTEXT`。正文采用顺序编码引用，例如“采用有限波数窗的二维谱合成方法生成高度场 [1,3]”。

文末引用列表严格按来源类型书写：

- 本地上传文献：只写文献编号，例如 `[1] 文献3`；不要求标题、作者、路径或网址。
- 外部网络资料或公开数据库：写可直接访问的网址，例如 `[2] https://example.org/dataset`。
- GPT 自身已有知识：简要说明所用知识及适用边界，例如 `[3] GPT 自带知识：二维随机场谱合成与实值场共轭对称条件；作为通用数值方法使用。`

同一来源在同一文件内复用同一顺序编号；一个公式或结论由多个来源共同支持时写成 `[1,3]`。工程固定上下文不是论文来源，相关约束直接用事实 ID 标注为“工程事实：`FACT.ID`”，不混入顺序参考文献编号。

该文件：

- 只保存到本轮 `runs/<MODULE>/CITATION_BRIEF.md`；
- 不并入 `MODULE_CONTEXT`、`INTEGRATED_MODEL` 或合同；
- 不作为下一轮输入，不参与工程事实审批，也不触发任何交互；
- 只有在完整机理形成后且人工明确要求时，才由 Codex 对各轮引用说明做轻量去重和整合。

## 7. 阶段快照和本地归档

每轮完成后由 Codex 按 `docs/derivation_workflow/guides/RUN_ARTIFACT_HANDLING_GUIDE.md` 执行：

1. 保存执行提示词；
2. 保存输入文件及版本清单；
3. 保存 Pro 原始回答；
4. 单独保存 `CITATION_BRIEF.md`，不把它加入任何后续默认输入；
5. 检查工程事实候选与当前正式版的差异；
6. 检查机理内容是否错误进入工程事实；
7. 保存本轮结束后的完整 `MODULE_CONTEXT` 快照；
8. 将通过审查的版本更新为 `current/MODULE_CONTEXT.md`；
9. 将关键工程事实变化提交人工确认。

其中格式修复、YAML 解析、字段补齐、路径核对、候选与基线 diff、生成器运行和归档命名均由 Codex 自主完成。不得要求人工检查模板占位符、排查 YAML、执行命令或判断纯格式差异。

阶段快照用于追溯和返工，不默认上传给下一子模块。相邻快照的 diff 用于判断 A2、A3 等阶段分别改变了什么。

## 8. 大模块集成

三个子模块按顺序完成后，必须新开 Pro 任务执行大模块集成。

### 8.1 默认上传三个文件

以 A 模块为例：

1. 最新正式 `engineering_fixed_context.md`；
2. 最新完整 `A_MODULE_CONTEXT.md`，其中已包含 A1+A2+A3；
3. `A_INTEGRATION_PROMPT.md`。

默认不上传 A1/A2/A3 阶段快照，也不重新上传原始论文。若集成发现信息丢失、证据冲突或模型假设不成立，再补充目标快照或对应文献包。

各子模块的 `CITATION_BRIEF.md` 即使在集成阶段也不默认上传。

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

提交人工确认时只报告经过机械校验后的语义问题，例如是否接受新的工程范围、数值、开关或边界。解析错误、字段缺失、路径问题和可无歧义修复的格式偏差由 Codex 先行处理，不作为人工问题上报。

## 11. 默认不上传的内容

除非出现明确审计需要，以下内容只做本地存档：

- 历史提示词和提示词草稿；
- 旧版 `MODULE_CONTEXT`；
- Pro 原始回答；
- 输入清单和文本 diff；
- 被否决的模型和临时计算；
- 备用文献包；
- 各轮 `CITATION_BRIEF.md`；
- 已经被下游合同压缩的上游完整推导。

该规则的目的不是删除信息，而是避免无关历史占用当前 Pro 任务的上下文。
