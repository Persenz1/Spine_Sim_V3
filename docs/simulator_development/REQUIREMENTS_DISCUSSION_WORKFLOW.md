# 模块需求讨论工作流

**版本：** 0.1.1

## 1. 两类窗口严格分开

每个模块使用两个窗口：

1. **需求讨论窗口**：理解模块、提出默认方案、与用户讨论参数/输出/图形/验收，冻结需求和实现提示词；不得写求解器代码。
2. **实现窗口**：完整读取冻结需求和实现提示词后编码、测试、运行模块样例；不得重新扩大产品范围。

当前 `prompts/requirements_discussion/` 中只提供第一类提示词。实现提示词必须由对应讨论窗口根据最终决定生成，不能预先用通用模板替代。

### 1.1 权威文件与证据副本

- 所有模块先从 `theory/README.md` 确认本任务的最短权威路径；
- A/B/C 层内公式和状态以 `theory/modules/` 为权威，`theory/interfaces/` 仅提供逐字一致的公共合同镜像；
- `theory/evidence_reassessment/` 是工程事实和文献提取的工作副本，用于查证与反向复核，不得升级为 accepted 模型或真实标定值；
- `archive/` 保留完整源文件、最终历史上下文和运行审计，普通需求讨论不得修改归档原件；
- 冻结需求必须记录实际读取的版本和路径，不能只写“见理论文件”。

## 2. 讨论窗口的交互方式

讨论窗口必须：

- 先读取权威文件和仓库现状，再提出建议；
- 先给出有理由的默认方案，不把所有设计责任推给用户；
- 每轮最多集中询问 1–3 个真正影响需求的问题；
- 参数、输出和图形分别讨论，避免混成一个长问卷；
- 明确记录 `accepted / rejected / deferred / unresolved`；
- 对缺少实验数据的量默认采用 DEV_PRIOR/扫描或 unavailable，不索要不存在的数据；
- 用户明确说“定了/冻结/按这个做”后才把状态改成 `frozen`。

## 3. 每个冻结需求文件的最小结构

`requirements/<MODULE>_REQUIREMENTS.md` 至少包含：

1. 身份、版本、状态和权威输入；
2. 用户目标与首版使用场景；
3. 范围、非目标和依赖；
4. 术语、坐标、单位与参数所有权；
5. 参数表：名称、符号、类型、单位、默认/范围、来源、是否扫描；
6. 输入 API 与前置状态；
7. 求解或处理流程的语义要求；
8. canonical raw output 合同；
9. 派生摘要与不可替代的原始字段；
10. 模块首批图、可选图和交互控制；
11. 状态、事件、错误与 unavailable 行为；
12. 数值/统计/性能/重放要求；
13. 单元、回归和验收测试；
14. schema/API 兼容与迁移；
15. 明确延期项；
16. 决策日志和仍需关闭的问题；
17. 实现窗口的完成判据。

## 4. 输出字段冻结规则

每个字段必须说明：

- 物理语义；
- 数据类型和形状；
- 单位；
- 表达 frame 与 reference point；
- entity/path/event 索引；
- accepted、trial、event、summary 中的归属；
- 是否 canonical raw、derived 或 diagnostic；
- 缺失时使用 null/unavailable 还是禁止整个请求；
- 采样时机与保存频率；
- schema 版本。

trial、事件定位和回滚中的值不得混入 accepted 物理曲线。滤波值、评分和峰值不得替代原始连续记录。

## 5. 绘图模块的特殊边界

M06 只读取：

- ResultReader 公共 API；
- schema/field metadata；
- canonical result bundle；
- 与绘图有关的配置和样式。

M06 不得读取或调用：

- A/B/C 内部对象；
- 求解残量函数；
- trial/commit 接口；
- surface evaluator；
- 运行器的重新执行入口。

派生数据写入与 canonical bundle 分离的目录，并包含 source run hash、recipe version、参数和生成时间。

## 6. 绘图数据缺口请求

如果图形无法由现有数据正确生成，M06 输出：

```text
PLOT_DATA_GAP_REQUEST:
  request_id
  requesting_recipe
  owning_source_module
  missing_field_semantics
  why_existing_fields_are_insufficient
  entity/path/event indexing
  data_type_and_shape
  unit/frame/reference_point
  required_sampling_cadence
  raw_or_derived_classification
  estimated_storage_cost
  additive_or_breaking_schema_change
  backward_compatibility_expectation
  validation_plot_or_test
```

请求本身不授权修改源模块。源模块必须在自己的后续窗口审查、实现并升级 schema。

## 7. 讨论窗口结束协议

用户确认需求后，讨论窗口必须：

1. 写入对应 `requirements/<MODULE>_REQUIREMENTS.md`；
2. 根据冻结需求生成 `implementation_prompts/<MODULE>_IMPLEMENTATION_WINDOW_PROMPT.md`；
3. 校验所有链接、参数状态、输入/输出闭合和与上游合同的一致性；
4. 明确列出延期项和首版不做内容；
5. 提交并推送本次需求产物；
6. 最终报告需求版本、提交号和下一实现窗口提示词；
7. 停止，不得在同一窗口开始编码。
