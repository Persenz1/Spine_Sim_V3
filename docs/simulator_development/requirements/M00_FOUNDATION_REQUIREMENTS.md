# M00 FOUNDATION 冻结需求

**需求标识：** `M00_FOUNDATION_REQUIREMENTS`

**需求版本：** `1.0.0`

**状态：** `frozen`

**冻结日期：** `2026-07-18`

**适用实现：** M00 基础契约、配置、事务外壳和结果 API

**后续窗口：** [M00 实现窗口提示词](../implementation_prompts/M00_FOUNDATION_IMPLEMENTATION_WINDOW_PROMPT.md)

## 1. 权威输入、目标和来源身份

### 1.1 实际权威输入

本需求冻结时完整读取并使用了以下文件：

- [仓库 agent 规则](../../../AGENTS.md)；
- [项目 README](../../../README.md) 与 [theory 阅读入口](../../../theory/README.md)；
- [仿真器开发入口](../README.md)；
- [模块规划](../SIMULATOR_MODULE_PLAN.md)；
- [需求讨论工作流](../REQUIREMENTS_DISCUSSION_WORKFLOW.md)；
- [证据复核入口](../../../theory/evidence_reassessment/README.md)；
- [工程固定上下文 1.0.0](../../../theory/evidence_reassessment/engineering_fixed_context.md)；
- [独立复核报告](../../../theory/review/DERIVATION_VERIFICATION_2026-07-17.md)；
- [开发期参数政策 0.1.0-dev](../../../theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md)；
- [DEV_BOOTSTRAP_PROFILE 0.1.0](../../../theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml)；
- [SYSTEM_INTEGRATED_MODEL 1.0.0](../../../theory/system/SYSTEM_INTEGRATED_MODEL.md)，全文读取并重点核对第 25–30、40–45 节。

权威顺序固定为：正式工程事实 > accepted system 的全局协调 > accepted A/B/C 的层内机理与模块内嵌合同。`theory/interfaces/` 只是合同镜像。复核报告中的 P0 是实现安全边界。proposed 文件不得静默修改 accepted 1.0。

### 1.2 用户目标和首版使用场景

M00 为无实验数据的 A/B 趋势筛选仿真器提供稳定、严格、可扩展、可重放的数据外壳。第一版必须完整支持：

`DEV_PRIOR / synthetic_surface / no_damage / not_certifiable`。

M00 的使用者包括 M01–M05 的数据生产者、M06 只读绘图消费者、M07 首版集成以及以后受限的 M08 诊断。M06 只能使用公开 ResultReader、schema 和字段元数据，不能导入或调用仿真内部对象。

### 1.3 来源身份映射

每项会改变 API、字段、配置、状态、测试或认证语义的决定必须保存具体来源引用。来源身份使用：

| 身份 | M00 用途 |
|---|---|
| `FIXED_ENGINEERING` | 工程目标、N–mm–MPa 主单位、坐标约定、100 mm A/B 路径等正式事实；不得覆盖 |
| `ACCEPTED_AUTHORITY` | accepted system 的对象边界、accepted/trial/event/transaction、输出和认证语义，以及本冻结需求自身的公共合同 |
| `PROPOSED_SUPPLEMENT` | 隔离的 additive 字段、诊断或验证结构；默认查询和排名不启用 |
| `DEV_POLICY` | DEV profile、存储 codec、分块、开发期性能基线和 `not_certifiable` 标签 |
| `VALIDATION_ONLY` | 解析 fixture、故障注入、兼容性样例、M00 无物理 demo；不得进入生产物理结果 |

字段的规范来源、运行值来源和具体 authority references 必须分开保存，不能压成一个 `provenance` 字符串。

## 2. 范围、非目标和依赖

### 2.1 M00 负责

- 配置 schema、严格解析、覆盖、单位规范化和 resolved config；
- run/case/design/seed/surface/state/event/receipt 的 ID、hash 和 lineage；
- 来源、成熟度、状态、失败和认证公共词汇；
- immutable、accepted、trial、event、transaction 和 output 的对象合同；
- ResultExtensionDescriptor、ResultWriter、ResultReader 和字段元数据查询；
- canonical result bundle、完整性、schema 演化和旧结果读取；
- deterministic replay manifest、事务幂等、故障恢复和公共验收 fixture；
- 每个模块 README 中简短的人类可读“输出概览”合同。

### 2.2 M00 不负责

- 任何接触、摩擦、梁、弹簧、表面、阵列、损伤或 C 层物理；
- Newton、事件定位、活动集、平衡或物理 commit eligibility；这些由 M02 和物理所有者决定；
- case 设计矩阵、并发调度和统计停止；这些由 M05 决定；
- 绘图配方、滤波、峰值检测、对齐、主题和导出；这些由 M06 决定；
- 实验数据采集、材料标定、二元成功阈值和综合评分；
- 实现 M01 或任何后续模块。

依赖方向必须保持：物理模块导入 M00 公共协议并注册扩展；M00 不导入物理模块。

## 3. 术语、单位和参数所有权

### 3.1 规范单位

内部唯一使用：

| 量 | 规范单位 |
|---|---|
| 长度、位移、事件位置 | mm |
| 力 | N |
| 应力、强度、弹性模量 | MPa = N/mm² |
| 平移刚度 | N/mm |
| 力矩、功、能量 | N·mm |
| 时间 | s |
| 速度 | mm/s |
| 角度 | rad |
| 断裂能 | N/mm |
| 无量纲量 | 1 |

外部输入允许显式 `{value, unit}` quantity；为兼容现有 DEV profile，允许版本化 suffix adapter 读取 `*_mm`、`*_N`、`*_MPa`、`*_N_per_mm` 等字段。除此以外，有量纲字段不得使用裸数。转换只在配置边界执行一次；下游只接收规范值。

必须保存原值、原单位、转换器 ID/version、规范值和规范单位。`50 um` 与 `0.05 mm` 的源文件 hash 不同，但规范化后的语义 hash 应相同。

### 3.2 M00 配置参数表

| 名称 | 类型/单位 | 冻结默认或范围 | 所有权 | 来源身份 | 具体来源 | 是否扫描 |
|---|---|---|---|---|---|---:|
| `hash_algorithm` | enum | `SHA-256` | NUMERICAL_CONFIGURATION | ACCEPTED_AUTHORITY | M00 1.0 冻结讨论；SYSTEM 第 25、40 节 | 否 |
| `config_authoring_format` | enum | 严格 YAML 1.2 子集；JSON 可输入 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 冻结讨论 | 否 |
| `canonical_numeric_dtype` | dtype | `float64` | NUMERICAL_CONFIGURATION | DEV_POLICY | M00 1.0 冻结讨论；SYSTEM 原始输出保真要求 | 否 |
| `parquet_compression` | enum | lossless Zstandard | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 冻结讨论 | 可调 |
| `zarr_format` | integer | 3，记录实际规范修订 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 冻结讨论 | 否 |
| `zarr_codec` | record | little-endian + Blosc/Zstandard + shuffle + CRC32C | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 冻结讨论 | 可调 |
| `parquet_row_group_target` | bytes | 约 32 MiB 未压缩 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 性能基线 | 可调 |
| `zarr_inner_chunk_target` | bytes | 约 4–8 MiB | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 性能基线 | 可调 |
| `zarr_shard_target` | bytes | 约 128 MiB | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 性能基线 | 可调 |
| `rejected_trial_diagnostic_level` | enum | `summary`；`none/summary/full` | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 冻结讨论；SYSTEM trial/accepted 隔离 | 可调 |
| `reader_batch_rows` | positive integer | 实现基于内存预算选择并记录 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | M00 1.0 性能基线 | 可调 |

codec、chunk 和 batch 改变存储性能，不得改变 semantic content hash 或物理结果。schema 不提供隐含物理或数值默认；所有值必须来自显式 profile 或 resolved config。

## 4. 配置层级、覆盖和 resolved config

### 4.1 层级

~~~text
L0  schema/vocabulary（无物理值）
L1  FIXED_ENGINEERING + ACCEPTED_AUTHORITY（锁定）
L2  DEV_POLICY profile
L2-isolated  PROPOSED_SUPPLEMENT / VALIDATION_ONLY
L3  experiment/run base config
L4  design/case/seed/surface patch
L5  recorded run override
~~~

后层只在字段所有权允许时覆盖前层。`FIXED_ENGINEERING` 和锁定的 `ACCEPTED_AUTHORITY` 不得由普通 override 修改。`PROPOSED_SUPPLEMENT` 和 `VALIDATION_ONLY` 使用隔离 namespace，不能 shadow accepted 物理字段。

### 4.2 合并规则

- map 按路径深合并；
- list 整体替换，不按位置合并；
- `null` 不表示删除；
- 声明字段不得被覆盖层删除；
- 每次覆盖保存 source layer、文件、字段路径、原值、结果值和锁状态；
- CLI override 必须先物化为 immutable override artifact；环境变量不得直接覆盖物理或数值配置。

### 4.3 严格校验

必须拒绝未知字段、重复键、非法 enum、维度错误、越界、NaN/Inf、含混类型强制转换、YAML anchor/merge/custom tag 和隐式日期。错误必须一次聚合报告：error code、字段路径、来源文件/层、原值和建议修复。

除字段级校验外必须执行跨字段约束、所有权锁、来源身份、单位维度、ID 引用、frame/reference point、schema 版本和能力覆盖校验。

### 4.4 resolved config

每个 run 生成 immutable `resolved_run_config`，每个 case 生成完全展开的 `resolved_case_config`。每个叶字段必须包含：

~~~text
canonical value/unit
parameter ownership
requirement origin
runtime value provenance
source file/path/hash
original value/unit
override chain
locked status
schema version
~~~

resolved config 不再依赖 include、环境变量、工作目录或当前时间；其 canonical semantic form 参与 ID 和 replay hash。

## 5. 身份、ID、hash 和 lineage

### 5.1 混合身份策略

| 对象 | ID 规则 |
|---|---|
| `run_id` | UUIDv7；每次实际执行唯一 |
| `run_fingerprint` | resolved config、代码、模型、合同、registry 和输入来源的确定性 SHA-256 |
| `design_id` | 设计变量规范化赋值与 schema version 的内容身份 |
| `seed_id` | RNG algorithm/version、stream namespace 和原始 seed 的内容身份 |
| `case_id` | design、seed、surface spec、operation/profile 和 case config 的内容身份 |
| `surface_spec_id` | generator family、domain、参数和算法版本的内容身份 |
| `surface_realization_id` | surface spec + seed + generator version 的内容身份，并另存实际内容 hash |
| `state_id` | parent state 与 canonical accepted-state manifest 的内容身份 |
| `event_id` | 仅 committed event；绑定 pre-state、实体、事件种类、定位结果和 cascade ordinal |
| `receipt_id` | parent、candidate hash、幂等键和有序 intents 的内容身份 |

完整 SHA-256 必须永久保存；短前缀只用于显示并必须做碰撞检查。`hash_profile_id/version` 固定 canonical JSON、decimal、array dtype/shape/endianness、map ordering 和非语义字段排除规则。

`trial_id` 属于运行实例 namespace。rejected trial 不获得 committed `event_id` 或 accepted `state_id`。

### 5.2 semantic hash

semantic hash 必须基于未压缩、单位规范化后的内容。压缩级别、chunk layout、绝对路径、生成时间和文件系统顺序不进入 semantic hash。源 artifact 另外保存字节级 SHA-256。

## 6. 来源、成熟度、状态和失败分类

### 6.1 来源查询

schema、table、field、algorithm、record 和 run 都必须可查询：

- `requirement_origin`；
- `value_provenance[]`；
- `authority_refs[]`，包含 path/ID、version、hash 和 locator；
- governing identity 与所有 contributing identities。

来自 accepted schema 但使用 DEV_PRIOR 值的结果仍为 `DEV_PRIOR/not_certifiable`。

### 6.2 四栏成熟度

必须分别保存：

~~~text
theory_defined
code_implemented
numerically_verified
experimentally_validated
~~~

每栏记录 `NOT_ASSESSED / SPEC_DEFINED / IMPLEMENTED_NOT_RUN / PASSED_WITH_EVIDENCE / FAILED / BLOCKED_UNAVAILABLE / NOT_APPLICABLE`、scope、version/hash 和 evidence refs。四栏不能合成为 `complete`。

### 6.3 多轴状态

`null` 只表示没有值，不能表示原因。可空输出必须关联：

~~~text
value_presence:
  PRESENT | NULL
capability_status:
  SUPPORTED | UNAVAILABLE | UNSUPPORTED | NOT_APPLICABLE
attempt_outcome:
  NOT_ATTEMPTED | ACCEPTED | REJECTED_TRIAL |
  CERTIFICATION_REJECTED | NUMERICAL_FAILURE | TRANSACTION_FAILURE
physical_feasibility:
  NOT_ASSESSED | FEASIBLE | PHYSICAL_INFEASIBLE
certification_status:
  NOT_ASSESSED | NOT_CERTIFIABLE |
  CERTIFICATION_BLOCKED | CERTIFIED_FOR_DECLARED_SCOPE
~~~

同时保存 `reason_code`、说明、authority refs 和 `last_valid_state_id`。`PHYSICAL_INFEASIBLE` 只有在合同、模型、参数、域、事件定位和数值证据充分时可用。`NUMERICAL_FAILURE`、`UNAVAILABLE` 或 `UNSUPPORTED` 不得推断物理不可行。

## 7. 对象所有权和事务边界

### 7.1 对象层

~~~text
Immutable:
  authority/schema/config/unit/frame/reference/transform/surface identities
Accepted:
  module-owned opaque state snapshots + SystemAcceptedStateManifest
Trial:
  side-effect-free candidate objects and NumericalTrialCache
Event:
  EventCandidate | CommittedEventRecord
Transaction:
  intent / rollback token / prepare token / commit bundle / receipt
Output:
  immutable records referring to accepted states and committed receipts
~~~

M00 拥有对象合同和持久化原子性；M02/物理模块拥有 trial 过程和物理 commit eligibility；M05 拥有 case 调度。M00 不解释物理状态内容。

### 7.2 事务链

~~~text
parent accepted
→ side-effect-free trial
→ candidate intents
→ prepare
→ atomic commit
→ receipt
→ accepted point / committed events publication
~~~

`prepare` 只校验 parent、版本、读写集合、hash、幂等键和持久化可用性。commit 必须使 accepted state、point、events、账本增量和 receipt 同时可见。没有最终 commit marker/receipt 的 staging 数据不是 accepted。

相同幂等键与相同 candidate 必须返回原 receipt；相同键与不同 candidate 必须返回冲突。失败恢复不得产生部分可见状态。

### 7.3 四类物理隔离

~~~text
accepted_points/
committed_events/
rejected_trials/
summaries/
~~~

summary 默认只能消费 accepted points 和 committed events。失败统计必须进入明确命名的 diagnostic summary。rejected trial 不推进 path/time/slip/damage/work/event/peak，也不能进入物理曲线或设计排名。

## 8. canonical result bundle

### 8.1 目录与格式

~~~text
<run_id>.spine-result/
├── bundle_manifest.json
├── schemas/
├── config/
├── provenance/
├── replay/
├── indices/
├── accepted_points/
├── committed_events/
├── rejected_trials/
├── summaries/
├── arrays/
├── transactions/
└── integrity/
~~~

- JSON：manifest、registry、resolved config、provenance 和 replay；
- Parquet：索引、point/event/trial/summary/receipt 的列式表；
- Zarr v3 core：固定类型、分块、多维数组；
- 每个 case 使用独立 immutable shard，run index 是可重建索引，不是物理所有者；
- optional archive 仅作传递；canonical 工作形式是目录 bundle。

CSV/JSONL、pickle、NPZ、SQLite-only 或单体 HDF5 不得作为 canonical 主格式。

### 8.2 表和关系

accepted points 至少分为 `common/per_unit/per_needle/per_support`；event 至少分为 `events/dependencies/cascade_rounds`；rejected trial 至少有公共诊断和可选完整 payload；summary 按 case/design/失败诊断分栏。

关系只能通过注册 ID 建立。模糊 many-to-many join 必须显式声明，禁止隐式笛卡尔积。

### 8.3 精度、missing 和压缩

canonical physical numeric 默认为 IEEE-754 float64；canonical accepted 数据不得用 float32 或有损量化。Zarr 可空数组必须使用独立 validity/status 数组；不得用 NaN 表示 missing。数值失败产生的 NaN/Inf 只能进入 rejected diagnostic 并带失败状态。

### 8.4 M00 核心输出表

所有模块扩展都必须引用下列公共基表，不能另建竞争 run、state、event 或 receipt 身份。

`RunEnvelope` 至少包含：

~~~text
run_id / run_fingerprint / operation_kind / operation_profile
result_api_version / bundle_schema_version / registry_hash
engineering/model/contract versions and hashes
solver_build_id / git_commit / dirty_status
resolved_run_config_id/hash
source_file_hashes
case/design/seed/surface indices
unit/frame/reference/transform registry IDs
first-release provenance and certification labels
replay_manifest_id/hash
created_at_utc_ns (non-semantic)
~~~

`AcceptedPointBase` 至少包含：

~~~text
run_id / case_id / design_id / seed_id / surface_realization_id
point_id / accepted_point_index
accepted_state_id / parent_state_id / commit_receipt_id
operation_kind / stage / path_kind
path_coordinate / path_unit / accepted_increment
physical_time_value / value-status tuple
event_sequence / simultaneous_group_ids / cascade_ids
module_payload_refs
residual/graph/quality/work-ledger refs
source/maturity/certification summary
request_hash / response_hash / replay_step_hash
~~~

`CommittedEventBase` 至少包含：

~~~text
event_id / source_event_ids / hierarchy / entity IDs
run/case/design/seed/surface IDs
event_kind
raw dimensional event function / unit / numerical scaling ID
path coordinate / bracket / fraction basis / localization error
pre_event_accepted_state_id
event_point_trial_id
post_event_accepted_state_id or explicit null-status
simultaneous_group_id / dependency edges / cascade round
pre/event/post payload refs
recoverability / stability / terminal classification
all status codes / uncertainty / certification
committed=true / commit_receipt_id
~~~

`RejectedTrialBase` 至少包含：

~~~text
trial_id / run_id / case_id / parent_accepted_state_id
request_hash / candidate_hash / requested path target
capability_status / attempt_outcome / physical_feasibility
reason_codes / diagnostic_summary / optional_full_payload_ref
last_valid_state_id
accepted_state_advanced=false
committed_event_id=null
commit_receipt_id=null
~~~

`SummaryBase` 至少包含：

~~~text
summary_id / summary_kind / schema_version
algorithm_id/version/hash
source_bundle_hash
source receipt range or receipt-set hash
included dataset classes and status filters
case/design/seed/entity scope
output field IDs
source identity / maturity / certification
created_at_utc_ns (non-semantic)
~~~

`CommitReceiptBase` 至少包含：

~~~text
receipt_id / idempotency_key
parent_state_id / committed_state_id
candidate_hash / ordered_intents_hash
schema/registry/config hashes
published shard and ledger hashes
commit sequence
commit marker hash
~~~

物理模块只能向 `module_payload_refs` 和注册扩展表添加自己的字段。公共 ID、状态、receipt 和 lineage 语义由 M00 唯一拥有。

## 9. 字段元数据和模块扩展

每个字段必须声明：

~~~text
field_id / namespace / owner_module
physical or processing semantics
canonical_raw | derived | diagnostic
dtype / shape / dimensions / raggedness
unit / frame / reference_point
sign and action semantics
entity/path/event indices
sampling cadence and storage frequency
accepted/trial/event/summary ownership
value/status/null policy
source identity and authority refs
four maturity columns
introduced/deprecated versions
storage dataset / encoding / precision
required or optional
~~~

有向量、wrench 和 pose 缺少 unit、frame 或 reference point 时不得注册或写入。

物理模块通过 declarative `ResultExtensionDescriptor` 注册 namespace、owner、extension schema version、tables、fields、arrays、common keys、source identity、maturity 和 compatibility class。M00 不导入物理模块；namespace 冲突或覆盖核心字段必须拒绝。

registry snapshot 在 run 启动时冻结并参与 run fingerprint。

## 10. ResultWriter 公共合同

M00 至少提供以下语义能力：

~~~text
register_extension_schema()
create_run_bundle()
write_resolved_config_and_provenance()
create_case_shard()
begin_transaction(parent_state_id, idempotency_key)
stage_accepted_point()
stage_committed_events()
stage_state_and_ledger_references()
prepare()
commit() -> receipt
rollback()
record_rejected_trial()
write_versioned_summary()
finalize_case()
publish_run_manifest()
~~~

Writer 只接受已注册的强类型记录，不提供绕过 schema 的任意 `write_dict`。Writer 必须校验 required fields、dtype/shape、单位、frame、reference point、source/maturity/status、state/event/receipt 链和 partition ownership。

## 11. ResultReader 与绘图公共合同

M06 只能依赖 ResultReader、FieldMetadata、DatasetCatalog、QueryResult/ChunkedArrayView 和 PLOT_DATA_GAP_REQUEST。不得直接读取 Parquet/Zarr 路径。

最低 API 语义：

~~~text
ResultReader.open(bundle_uri, verify_mode)
bundle_info()
list_datasets()
list_fields(selector)
describe_fields(field_ids)
list_relations()
query(dataset, fields, filters, joins, ordering, batch_size)
series(x_field, y_fields, group_by, filters, entity_scope)
events(filters, event_window, include_sides={pre,event,post})
open_array(field_id, case_selector, entity_selector, slice_spec)
resolve_lineage(state_ids | event_ids | receipt_ids)
check_plot_requirements(PlotDataRequirements)
build_plot_data_gap_request(report, recipe_identity)
~~~

tabular 查询返回只读 batch iterator；大数组返回只读 chunked view。每次查询返回 QueryManifest，包含 bundle/schema hash、字段、过滤、join、排序、显式单位/frame view 和结果 hash。

Reader 默认只自动列出 `FIXED_ENGINEERING / ACCEPTED_AUTHORITY / DEV_POLICY` 的 accepted/committed 数据。`PROPOSED_SUPPLEMENT / VALIDATION_ONLY`、rejected trial 和 diagnostic 字段必须显式 opt-in，且默认禁止进入设计排名。

Reader 不隐式插值、重采样、滤波、平滑、峰值检测、对齐或改变 reference point。显式、审计过的只读单位/frame/reference view 可以生成，但不能修改 canonical 值。

若配方字段不存在、cadence 不足、frame/reference 不兼容或来源身份不允许，Reader 必须生成结构完整的 `PLOT_DATA_GAP_REQUEST`。请求不授权修改源模块。

## 12. schema/API 演化和旧结果读取

### 12.1 版本规则

`result_api_version`、`bundle_schema_version`、核心 schema 和每个 extension schema 均采用 SemVer。

- PATCH：文档、校验或实现修复，不改变字段语义；
- MINOR/additive：新增 optional field/table/enum capability，旧字段语义不变；
- MAJOR/breaking：改变字段含义、dtype、unit、frame、reference point、indexing、requiredness、状态或事务语义。

物理字段语义变化必须创建新 field ID 或 major version；不得就地改写旧字段。

### 12.2 reader 行为

- 同一 major 的所有旧 minor 必须向后可读；
- newer minor bundle 被旧 reader 打开时，只允许读取已知字段并显式返回 `PARTIAL_SCHEMA_SUPPORT`；不得静默导出未知字段；
- newer reader 读取旧 bundle 时，缺失的新字段返回 `NULL + UNAVAILABLE + FIELD_NOT_PRESENT_IN_SCHEMA_VERSION`，不得填默认值；
- major 不兼容必须返回 `BREAKING_SCHEMA_UNSUPPORTED`，同时仍可读取最小 manifest、版本和来源信息；
- 跨 major 迁移必须使用版本化 adapter，写出新 bundle 和 migration lineage，绝不原地修改旧 bundle；
- 仓库必须维护兼容矩阵和旧 bundle fixture。

## 13. deterministic replay

ReplayManifest 至少保存：

- run ID/fingerprint、schema/API/hash/canonicalization versions；
- resolved run/case config 与全部 source/semantic hashes；
- Git commit、dirty status、solver build ID 和模块/合同版本；
- registry、unit/frame/reference/transform 和 boundary manifests；
- RNG algorithm/version、root seeds、stream namespaces 和归约顺序；
- surface generator/spec/realization identities；
- Python/runtime、OS/architecture、关键依赖、数值 backend、线程和浮点归约设置；
- parent state/receipt chain、idempotency keys 和 case execution plan；
- determinism profile、field tolerances 和 diagnostic level。

定义两级重放：

1. `BITWISE_REPLAY`：相同支持平台、backend 和 determinism profile 下 semantic IDs、accepted arrays、events 和 receipts 位级一致；
2. `SEMANTIC_REPLAY`：跨兼容平台时状态、事件序列和失败分类一致，数值量在字段级版本化容差内一致。

不同压缩/chunk layout 必须产生相同 semantic content hash。串行和并行 case 执行不得改变单 case 物理结果；规范归约顺序必须记录。重放差异必须形成结构化 report，不能只返回 pass/fail。

## 14. 性能、完整性和资源要求

标准 M00 I/O fixture 使用 1,000 cases、合计至少 1,000,000 accepted point rows、逐实体子表、事件、rejected diagnostics 和一个 chunked array。测试必须记录硬件、磁盘、OS、runtime 和依赖版本。

最低要求：

- 打开 bundle 和读取 catalog 不扫描 payload，参考本地 SSD 环境不超过 2 s；
- 字段目录查询在打开后不超过 0.5 s；
- 单 case 两字段、10,000 点 series 的首批结果不超过 1 s；
- 选择 8 个 float64 列扫描 1,000,000 rows 不超过 5 s；
- writer 生成标准 fixture 不超过 30 s；
- batch 读取 10 GiB logical bundle 时峰值额外 RSS 不超过 512 MiB；
- 单 case 查询只访问该 shard 和必要 manifest，不遍历其他 case payload；
- 4 个并发 case writer 不产生共享可变数据文件、部分提交或 hash 不确定性；
- full integrity verification 可更慢，但必须流式且内存有界。

性能未达标不得通过 M00 验收；可以调整 codec/chunk/batch，但必须保持 schema 和 semantic hash。

## 15. 单元、schema、重放和验收测试

### 15.1 单元测试

- 严格 YAML/JSON、duplicate/unknown key、覆盖、锁和错误聚合；
- 所有单位转换及重复转换拒绝；
- canonicalization、ID/hash、短 ID 碰撞和非语义字段排除；
- source/maturity/status 多轴组合；
- registry/namespace/field metadata；
- transaction prepare/commit/rollback、幂等和部分写失败；
- ResultWriter/Reader projection/filter/join/series/event/array/lineage；
- corruption、checksum、missing shard 和 stale manifest。

### 15.2 schema 与兼容测试

- 每个字段的语义、dtype、unit、frame/reference、index、source、maturity 和 null policy 完整；
- additive/minor、breaking/major、旧 reader/new reader 和 migration fixture；
- README 中引用的 dataset/field ID 必须真实存在；
- proposed/validation 字段默认 opt-in；
- rejected trial 不能通过任何默认查询混入 accepted 曲线。

### 15.3 重放与故障注入

- 同输入重复写的 semantic hash、state/event/receipt 一致；
- 不同 chunk/compression 的 semantic hash 一致；
- serial/parallel case 结果一致；
- prepare、data write、event write、receipt 和 manifest publish 各阶段故障均无部分 accepted 可见；
- retry 不重复累计；
- BITWISE 和 SEMANTIC replay 均有正例和负例。

### 15.4 最小无物理 demo

M00 必须使用 `VALIDATION_ONLY` fixture 写出并读回一个小 bundle，包含：

- 一个 run、design、seed、surface identity 和 case；
- resolved config、authority/source hashes 和 replay manifest；
- 至少两个 accepted points；
- 一个 committed event；
- 一个 rejected trial diagnostic；
- 一个 versioned summary；
- 一组模块 extension 字段和一个 chunked array；
- 完整 state/receipt lineage。

该 demo 不得实现或暗示任何接触、摩擦、梁、阵列或 C 物理。

## 16. 每个模块的人类可读输出概览

M00–M07，以及以后实现的 M08，必须在各自模块根目录 `README.md` 中提供简短的 `## 输出概览`。至少说明：

- 模块输出什么、由谁消费；
- canonical raw、event、diagnostic、summary 的核心 dataset；
- 关键索引、单位、frame/reference point；
- unavailable/unsupported/失败如何表达；
- 如何使用 ResultReader 查看最小 demo；
- 来源、成熟度和认证标签。

README 只做人类导航，不能复制或取代完整 machine-readable schema。README 引用的 dataset/field ID 必须自动校验。求解模块不得为展示删减 raw；M06 README 只介绍 figures、plot manifest 和 derived artifacts，不声称拥有仿真物理；M07 README 提供完整实验结果入口。

## 17. 明确延期和不做内容

- 不在 M00 实现任何求解器、事件定位算法、物理状态转换或绘图；
- 不定义 M01–M05 的具体物理扩展字段，只实现注册协议和 fixture；
- 不决定 M06 的图形类型、主题、滤波或派生算法；
- 不支持实时流式 UI、远程对象存储或分布式数据库作为首版完成条件；
- 不承诺跨不兼容 major 的无损自动迁移；必须显式 adapter 或清晰错误；
- 不把 `PROPOSED_SUPPLEMENT`、`VALIDATION_ONLY` 或 DEV_PRIOR 提升为 accepted/validated 物理；
- 不创建二元抓附成功或综合评分。

## 18. 决策日志

### 18.1 accepted

- 严格 YAML 1.2 子集/JSON、所有 override 物化、禁止环境变量暗改；
- 新 quantity 对象加版本化 suffix adapter；
- N–mm–MPa 内部单位且只换算一次；
- UUIDv7 run ID 与确定性 semantic IDs 并存；
- source origin、runtime value provenance 和 authority refs 分开；
- 四栏成熟度独立、证据化；
- null、能力、执行结果、物理可行性和认证状态分轴；
- accepted、trial、event、transaction、output 分层；
- accepted points、committed events、rejected trials、summaries 物理隔离；
- per-case immutable shard、原子 receipt publication 和幂等 retry；
- JSON + Parquet + Zarr v3 canonical bundle；
- canonical physical numeric float64、只允许无损压缩；
- validity/status 代替 NaN missing；
- 强类型 ResultWriter 和只读、可发现、lazy ResultReader；
- M06 只依赖 ResultReader/API，不直接依赖存储或求解器；
- proposed/validation/rejected diagnostics 默认 opt-in 且不进入排名；
- 模块通过 descriptor 注册扩展，M00 不反向导入；
- SemVer schema、显式 major migration 和旧 bundle fixture；
- BITWISE/SEMANTIC 两级 replay；
- 每个模块 README 提供简短“输出概览”。

### 18.2 rejected

- 隐式单位、frame、reference point、参数默认或类型转换；
- 用单一 `complete/success/provenance` 掩盖状态；
- trial/rejected values 进入 accepted 曲线、事件、功、峰值或排名；
- numerical failure 推断 physical infeasible；
- PROPOSED_SUPPLEMENT/VALIDATION_ONLY 覆盖 accepted 物理；
- Reader 扫目录猜测 accepted 数据或 M06 直接读物理文件；
- Writer 任意字典绕过 schema；
- canonical float32、有损压缩或 NaN missing；
- 单体 HDF5、SQLite-only、CSV/JSONL、NPZ 或 pickle 作为 canonical 主格式；
- 就地改变旧字段语义或原地迁移旧 bundle。

### 18.3 deferred

只延期远程对象存储、实时 UI、分布式 catalog、M06 具体配方和跨不兼容 major 的自动迁移。它们不阻断 M00 1.0。

### 18.4 unresolved

无。

### 18.5 需求讨论轮次留档

| 轮次 | 主题 | 冻结结果 |
|---:|---|---|
| 1 | 配置、单位与身份 | 用户接受严格配置、双显式单位入口和混合 ID/hash 默认方案 |
| 2 | 来源、成熟度与状态 | 技术结构由 Codex 按权威证据关闭；来源、四栏成熟度和多轴状态获纳入 |
| 3 | 事务对象 | 冻结 accepted/event/rejected/summary 隔离、原子 receipt、幂等和 per-case shard |
| 4 | 存储与读取 API | 冻结 JSON + Parquet + Zarr、float64/lossless、Writer/Reader 和模块扩展协议 |
| 5 | schema、重放、性能与验收 | 用户授权 Codex 自行关闭纯软件选择；本文件第 12–15 节为冻结结论 |
| 6 | 绘图交接 | 用户确认 M00 必须提供明确、可发现的输出和 ResultReader API，M06 在 M01–M05 demo 后讨论 |
| 7 | 人类输出说明 | 用户要求所有模块 README 提供简短精炼的输出概览；已进入本文件和中央工作流 |
| 冻结 | 留档、提交和推送 | 用户明确要求将本轮讨论留档并提交推送 |

## 19. 实现窗口完成判据

M00 实现窗口只有在以下全部满足时完成：

1. 本文全部 MUST 行为有代码、测试或明确不可用路径；
2. strict config、unit、ID/hash、status/maturity/source registry 通过测试；
3. transaction、bundle、Writer/Reader、extension、schema evolution 和 replay 通过故障注入与兼容测试；
4. 最小无物理 demo 可从干净环境生成、验证、读取并输出简短的人类可读概览；
5. M00 README 含 `## 输出概览` 且字段引用通过自动校验；
6. 性能 fixture 达到第 14 节最低要求；
7. 没有 solver、surface physics、A/B/C physics 或 plotting 反向依赖；
8. 所有结果明确为 `DEV_PRIOR / synthetic_surface / no_damage / not_certifiable` 或 `VALIDATION_ONLY`；
9. 文档链接、API signatures、schema registry 和 SYSTEM 输出外壳一致；
10. 实现窗口提交后停止，不自动开始 M01。
