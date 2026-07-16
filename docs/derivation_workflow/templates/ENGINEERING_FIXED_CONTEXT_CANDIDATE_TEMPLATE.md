# `engineering_fixed_context.md` 完整候选输出合同

> 规范源：`engineering_fixed_context/internal/README.md`、`manifest.yaml`、`schema.yaml`、`build_context.py` 以及当前通过校验的 `engineering_fixed_context.md`。
>
> 本文件只规定 Pro 如何输出人工审阅候选。正式工程事实的唯一维护方向始终是：
>
> `internal/facts/*.yaml → build_context.py → engineering_fixed_context.md`

## 1. 文件性质与禁止事项

1. 候选文件名为 `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`，它不是正式源，不得直接覆盖 `engineering_fixed_context/engineering_fixed_context.md`。
2. Pro 不得修改或输出替代版 `manifest.yaml`、`schema.yaml`、`build_context.py` 或 `internal/facts/*.yaml`。
3. 候选只允许承载能够映射到当前 schema 的工程事实；机理方程、状态机、接触算法、经验拟合和数值实现进入 `MODULE_CONTEXT`。
4. 不得在候选正文加入变更说明、审稿意见、引用附录、`candidate-from-*` 标头或其他生成器不会输出的内容。
5. `CITATION_BRIEF.md` 仅本地旁路归档，禁止作为正式事实的 `provenance.source`。

## 2. 基线与完整性要求

1. 以实际上传且已经通过以下命令校验的最新正式文件为唯一基线：

   ```powershell
   conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
   ```

2. 输出必须是完整 Markdown 文件，不得只输出 diff、修改片段或建议清单。
3. 若没有工程事实变化，候选必须与输入正式文件逐字一致；不得仅写“无变化”。
4. 若存在变化，所有未变化的标题、文件头、说明、状态图例、领域导航、事实条目、来源行和尾部“结构化源与生成信息”必须原样保留。
5. 候选身份由文件名和 `RUN_UPDATE_SUMMARY.yaml` 表示；候选正文仍保持生成器输出的正式文件头：

   ```markdown
   # 钩爪式爬壁机器人爪刺啮合求解器：工程固定上下文

   > 版本：`{正式基线版本}`
   > 状态：`current`
   > 本文件由 `engineering_fixed_context/internal/facts/*.yaml` 单向生成，是供人工审阅和网页端上传的完整工程事实视图。
   > 它只定义工程事实、边界、工况、接口要求和未决参数；具体机理实现属于 `RESULT` 与 `MODULE_CONTEXT`。
   ```

## 3. 候选正文必须遵守的渲染顺序

每条事实必须与 `build_context.py::render_fact` 保持同一顺序；不适用的可选段落直接省略，不写空标题：

1. `### FACT.ID — 标题`，事实 ID 不加反引号；
2. `状态`；
3. `适用范围`；
4. 可选 `符号`；
5. 可选 `取值`，单位由 `unit` 统一追加；
6. 必需的 `summary` 正文；
7. 可选 `定义` 表；
8. 可选 `工程表达`；
9. 可选 `必须满足`；
10. 可选 `约束`；
11. 可选 `说明`；
12. 可选 `登记项` 表；
13. 必需的来源行。

来源行格式固定为：

```markdown
> 来源：{provenance.source}，第 {provenance.section} 节；来源类型：{provenance.type}。
```

## 4. 每项变化必须伴随完整结构化映射

候选正文之外，`RUN_UPDATE_SUMMARY.yaml` 必须为每项 `add` 或 `modify` 提供一个完整 `proposed_fact`，且字段直接对应 `schema.yaml`。不得只给被修改的局部字段。

必需字段：

```yaml
id: SURFACE.EXAMPLE.ID
title: 示例标题
order: 6
status: unresolved
scopes: [solver, experiment]
summary: 示例工程事实摘要
provenance:
  type: run_candidate
  source: derivation/runs/{A1 | A1-r02}/RUN_UPDATE_SUMMARY.yaml
  section: engineering_context_delta.SURFACE.EXAMPLE.ID
```

允许的可选字段仅限：

```yaml
symbol: R_q
value: null
unit: mm
definitions:
  - term: 名称
    meaning: 含义
equations:
  - latex: z=h(x,y)
    label: 可选标签
    description: 可选说明
requirements:
  - 必须满足的工程要求
constraints:
  - 工程约束
notes:
  - 工程说明
registry:
  - id: SURFACE.EXAMPLE.UNRESOLVED
    topic: 未决项目
    scope: 可选作用域说明
    note: 可选备注
```

未使用的可选字段必须删除，不能用空字符串、空列表或 `null` 占位。虽然当前 `schema.yaml` 列出了 `dependencies`，但 `build_context.py` 尚不渲染该字段；为防止生成视图静默丢失信息，本模板禁止 Pro 新增或修改 `dependencies`，只能将相关关系写入 `MODULE_CONTEXT` 或未决问题。

## 5. schema 硬约束

### 5.1 事实 ID、顺序和位置

- 事实 ID 必须匹配 `^[A-Z][A-Z0-9_]*(\.[A-Z0-9_]+)+$`，并与全部事实 ID、登记 ID 全局不重复。
- `order` 必须是整数，并在所属领域内唯一。
- 新事实只能加入 `manifest.yaml` 已登记的九个既有事实文件之一；Pro 不得自行增加领域、事实文件或修改 manifest。
- `RUN_UPDATE_SUMMARY.yaml` 必须给出目标 `fact_file`、`domain_id`、`domain_order` 和 `fact_order`。

### 5.2 状态

`status` 只能取以下原始枚举值：

- `fixed`
- `fixed_set`
- `fixed_range`
- `model_switch`
- `interface_required`
- `unresolved`
- `excluded`

没有 `deprecated` 状态。本工作流也不允许 Pro 删除或 `deprecate` 既有事实；若认为既有事实不再适用，只能提出 `modify`，说明建议状态和影响，等待人工决定。

### 5.3 作用域

`scopes` 必须是非空列表，且只能使用：

- `global`
- `single_spine`
- `array_unit`
- `cross_gripper`
- `solver`
- `experiment`

候选 Markdown 中显示对应中文标签，但 `RUN_UPDATE_SUMMARY.yaml` 的 `proposed_fact.scopes` 必须保留上述原始英文枚举。

### 5.4 字段形状

- `definitions`、`equations`、`requirements`、`constraints`、`notes`、`registry` 必须是列表。
- 每个 `definitions` 项必须含 `term`、`meaning`。
- 每个 `equations` 项必须含 `latex`；LaTeX 字符串不含 `$$` 包围符。
- 每个 `registry` 项必须含合法且全局唯一的 `id` 与 `topic`。
- `symbol` 不含外层 `$`；渲染器会自动添加。
- `value` 必须保留正确的 YAML 原生形状：单值、列表或映射；不得为了排版把数值和单位拼成一个字符串，单位单独放在 `unit`。
- 模型开关值不得使用 YAML 隐式布尔值；使用带引号的字符串，例如 `"off"`、`"on"`。

## 6. provenance 与基线覆盖规则

1. `provenance` 必须同时包含 `type`、`source`、`section`。
2. `source` 必须是相对于仓库根目录的本地路径，且在正式写入 YAML 前真实存在；不得直接填网址。
3. 修改既有事实时，必须保留原事实的 `id`、`order` 和完整 `provenance`。原因是 `build_context.py` 会检查 `manifest.yaml` 中全部 `baseline_sections` 是否仍由原始基线来源覆盖。
4. 修改既有事实所依据的新论文、网址、自身知识和推导位置只写入 `RUN_UPDATE_SUMMARY.yaml.evidence`，不替换原始 provenance；正式接受后由 Codex同步记录本地 Changelog。
5. 新增事实可把本轮已归档的 `RUN_UPDATE_SUMMARY.yaml` 作为本地 provenance，例如：

   ```yaml
   provenance:
     type: run_candidate
     source: derivation/runs/{A1 | A1-r02}/RUN_UPDATE_SUMMARY.yaml
     section: engineering_context_delta.SURFACE.EXAMPLE.ID
   ```

6. 外部网址保存在该变更条目的 `evidence.external_urls` 中；本地上传论文编号保存在 `evidence.local_literature`；GPT 自身知识保存在 `evidence.gpt_knowledge`。

## 7. 操作边界

`engineering_context_delta.operation` 只允许：

- `none`：没有变化；候选与正式基线逐字一致；
- `add`：向既有领域新增一条 schema 合法事实；
- `modify`：输出一条既有事实修改后的完整映射，同时保留原 `id`、`order` 和 `provenance`。

不允许 `delete`、`deprecate`、静默改 ID、静默改顺序、静默拆分事实或静默合并事实。确有此类需求时，只记录为未决问题，交由人工和 Codex执行显式 schema/manifest 迁移。

当 `operation: none` 时，`RUN_UPDATE_SUMMARY.yaml` 中必须令 `target: null`、`changed_fields: []`、所有证据列表为空、`proposed_fact: null`、`approval_required: false`，不能保留模板占位字段。

## 8. 内容边界

允许进入工程事实候选：

- 坐标、方向、编号和单位；
- 几何尺寸、参数范围和扫描集合；
- 运动自由度、边界条件和加载工况；
- 模型开关、接口能力和输出要求；
- 首版排除项和尚未固定的参数。

禁止进入工程事实候选：

- 接触、摩擦、梁柔顺、活动集、损伤和载荷重分配的实现方程；
- 单刺、阵列或整爪状态机；
- A/B/C 模块推导过程；
- 未经人工批准而由论文、网址或 GPT 自身知识推断出的唯一工程数值。

外部证据不足以固定唯一数值时，使用 `unresolved`、参数范围、接口要求或登记项，不得硬编码。

## 9. 本地接受流程

Pro 只输出候选。Codex 审查并取得人工确认后：

1. 修改对应 `engineering_fixed_context/internal/facts/*.yaml`；
2. 如有正式版本变化，按项目版本规则修改 `internal/manifest.yaml`；
3. 运行：

   ```powershell
   conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --write
   conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
   ```

4. 检查生成后的正式 Markdown 与已批准候选语义一致；
5. 更新 `engineering_fixed_context/internal/CHANGELOG.md`。

任一步失败都不得发布新的正式工程事实。
