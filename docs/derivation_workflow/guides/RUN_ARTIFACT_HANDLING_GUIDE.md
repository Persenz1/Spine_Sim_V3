# 本地运行产物处理与机械审查指导

> 用途：规定 Codex 在每次网页端 Pro 运行前后如何处理输入清单、原始回答、候选文件、YAML、diff、校验和归档。
>
> 原则：这些工作由 Codex 自主完成，不要求人工参与机械检查。人工只决定工程事实和物理语义。

## 1. 执行前必须阅读

Codex 必须完整阅读：

1. `docs/derivation_workflow/DERIVATION_WORKFLOW.md`；
2. 当前任务提示词；
3. 当前任务适用的输出合同或模板；
4. `engineering_fixed_context/internal/README.md`；
5. `engineering_fixed_context/internal/schema.yaml`；
6. `engineering_fixed_context/internal/manifest.yaml`；
7. `engineering_fixed_context/internal/build_context.py`；
8. `engineering_fixed_context/internal/CHANGELOG.md`；
9. 本轮实际输入文件和已有运行目录。

## 2. 执行前由 Codex 完成

1. 建立正确的 `derivation/runs/<TASK>/` 目录；
2. 保存最终提示词为 `PROMPT.md`；
3. 根据提示词中的显式输入清单生成 `INPUT_MANIFEST.yaml`；
4. 核对文件存在、版本、路径和最小文献包；
5. 运行工程事实基线校验；
6. 确保提示词、输入清单和实际上传文件一致。

这些步骤不向人工提问，除非缺失的输入涉及无法推断的物理选择或权限边界。

## 3. 执行后由 Codex 自动拆分和归档

1. 原样保存完整回答为 `RAW_RESPONSE.md`；
2. 提取并保存本轮主结果；
3. 保存完整工程事实候选；
4. 解析并保存 `RUN_UPDATE_SUMMARY.yaml`；
5. 单独保存 `CITATION_BRIEF.md`；
6. 保存通过审查的当前上下文和历史快照；
7. 记录所有无歧义的机械修复。

`RAW_RESPONSE.md` 永远保留原样；机械修复作用于拆分后的候选文件，不回写伪装成原始回答。

## 4. Codex 可自主修复的机械问题

无需人工确认即可处理：

- Markdown 标题、代码围栏、空行和换行符；
- 文件名、目录名、相对路径和大小写；
- YAML 缩进、引号、空占位符和可确定的数据类型；
- 已知提示词版本、输入版本、模块编号和运行路径；
- schema 要求但可从正式基线无歧义补回的字段；
- 修改既有工程事实时误改的 `id`、`order` 或基线 provenance；
- `operation: none` 时将候选恢复为正式基线并清空占位字段；
- 模板残留占位符；
- 输入清单、快照名称和归档位置；
- diff 生成、字段排序和生成器命令执行；
- 能依据正式文件唯一确定的状态或作用域枚举映射。

所有修复必须不改变物理含义。若一种机械错误存在两个以上语义不同的修复方向，则停止自动修复，转入语义审查。

## 5. 必须自行完成的检查

### 5.1 运行摘要

- YAML 能解析；
- 必需字段完整；
- 未使用的可选字段已删除；
- ID、order、status、scopes 合法；
- provenance 完整且本地路径存在；
- 修改既有事实时保留基线 provenance；
- 没有生成器不渲染的隐藏字段。

### 5.2 工程事实候选

- 与正式基线做完整 diff；
- 未变化内容保持一致；
- 机理内容没有进入工程事实；
- 每项变化在运行摘要中有对应条目；
- 外部网址没有直接写成正式本地 provenance；
- 接受变化前后均能通过生成器校验。

### 5.3 模块结果

- 是最新完整上下文而非本轮增量；
- 范围、符号、方程、事件、接口、证据、验证和交接齐全；
- 没有因格式修复丢失公式、表格或未决问题。

### 5.4 引用说明

- 本地文献只按编号列出；
- 外部来源使用可直接访问的网址；
- GPT 自身知识有简短内容和边界说明；
- 文件只做本地归档，不进入后续交互链。

## 6. 不得要求人工参与的事项

不得让人工：

- 检查或修复 YAML；
- 比较长文件 diff；
- 判断路径和文件名；
- 运行生成器、格式化器或校验命令；
- 清理模板占位符；
- 判断纯格式变化；
- 维护输入清单、快照或 Changelog 的机械内容；
- 排查可由日志、schema 或正式基线确定的错误。

如果机械检查失败，Codex 应先读取错误、定位原因、修复并重新验证，不把错误原样转交人工。

## 7. 只有这些语义问题提交人工

- 是否接受新增或修改的工程事实；
- 是否改变已固定数值、扫描集合、坐标、边界、模型开关或首版范围；
- 两种物理机理或证据冲突需要选择；
- 缺失信息存在多个会实质改变模型的合理假设；
- 是否扩展到当前授权范围之外；
- 外部资料是否足以成为正式工程依据。

提交时只用自然语言说明：当前事实、候选变化、证据、影响和可选决定。除非人工主动要求，不展示 YAML 排障过程。

## 8. 验证命令基线

Python 项目命令使用既有 Conda 环境：

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

接受工程事实变化后：

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --write
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

任一校验未通过时继续由 Codex 排障；不得把未验证文件提交人工作机械验收。
