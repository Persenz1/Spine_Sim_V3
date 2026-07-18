# M00 FOUNDATION 实现窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。该窗口只实现冻结的 M00，不讨论或启动 M01。

## 提示词正文

~~~text
TASK_ID: M00_FOUNDATION_IMPLEMENTATION
PROMPT_VERSION: 1.0.1
REQUIREMENTS_VERSION: M00_FOUNDATION_REQUIREMENTS 1.0.0 frozen

本窗口只实现、测试和验收 M00 FOUNDATION：基础契约、严格配置、单位/身份、事务持久化外壳、canonical result bundle、ResultWriter/ResultReader、schema 演化和重放。不得实现任何表面、接触、摩擦、梁、弹簧、阵列、损伤、C 层物理或绘图代码；不得自动开始 M01。

开始前必须完整读取：
1. README.md、theory/README.md；
2. docs/simulator_development/README.md；
3. docs/simulator_development/SIMULATOR_MODULE_PLAN.md；
4. docs/simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md；
5. docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md；
6. theory/evidence_reassessment/README.md；
7. theory/evidence_reassessment/engineering_fixed_context.md；
8. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
9. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
10. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
11. theory/system/SYSTEM_INTEGRATED_MODEL.md，必须全文读取并重点复核第 25–30、40–45 节。

权威顺序：
正式工程事实 > accepted system 全局协调 > accepted A/B/C 层内机理与模块内嵌合同 > M00 冻结软件合同。若实现便利与冻结需求冲突，冻结需求优先；若冻结需求与更高物理权威存在实质冲突，停止并报告，不能静默修订需求或物理。

实现前：
- 读取 git status --short，保留所有既有工作区改动；
- 检查仓库当前语言、包、测试和 lint 约定；若没有既有 Python 包布局，采用 src/spine_sim/foundation 的 Python 3.12 typed package；
- 先形成简短实施计划和需求到测试的可追踪矩阵；
- 不重新讨论冻结产品范围，不向用户询问纯软件内部选择；
- 不读取 archive/，除非冻结需求中的当前文件无法闭合且明确报告原因。

必须实现：

A. strict config 与 resolved config
- 严格 YAML 1.2 子集和 JSON 输入；
- duplicate/unknown key、anchor/merge/custom tag、隐式类型、NaN/Inf 拒绝；
- L0–L5 层级、字段锁、map 深合并、list 整体替换、null 非删除；
- CLI 覆盖物化，不从环境变量隐式读取物理/数值配置；
- explicit {value, unit} quantity 和版本化 suffix adapter；
- N–mm–MPa 一次性规范化；
- resolved_run_config/resolved_case_config 和逐叶来源链。

B. identity、hash、source、maturity 和 status
- UUIDv7 run_id；
- SHA-256 canonical semantic identity 和 source byte hashes；
- design/seed/case/surface/state/event/receipt 的稳定内容身份；
- requirement_origin、value_provenance、authority_refs；
- theory_defined/code_implemented/numerically_verified/experimentally_validated 四栏；
- value presence、capability、attempt、physical feasibility、certification 多轴状态；
- null/unavailable/unsupported/numerical_failure/physical_infeasible 的冻结区别。

C. schema registry 与扩展
- M00 核心 schema、字段元数据和 relation catalog；
- ResultExtensionDescriptor；
- namespace/owner/version/compatibility 校验；
- 有向量字段的 unit/frame/reference point 强制校验；
- registry snapshot 冻结和 hash；
- 物理模块单向注册，M00 包不得导入任何未来物理模块。

D. transaction 和 canonical bundle
- immutable/accepted/trial/event/transaction/output 类型边界；
- per-case immutable shard；
- accepted_points、committed_events、rejected_trials、summaries 物理隔离；
- prepare、atomic publication、receipt、rollback、幂等和 crash recovery；
- JSON manifest/schema/config/provenance/replay；
- Parquet 表和 Zarr v3 chunked arrays；
- float64 canonical numeric、lossless codecs、validity/status arrays；
- semantic hash 与 chunk/compression layout 解耦；
- corruption/checksum/stale/missing shard 检测。

E. ResultWriter
- 实现冻结需求第 10 节的全部公共能力；
- 只允许已注册强类型记录；
- 不提供任意 write_dict 或未校验 escape hatch；
- staged candidate 只有 commit receipt 发布后才可见；
- rejected trial 永远不能获得 accepted state 或 committed event 身份。

F. ResultReader 与绘图边界
- 实现冻结需求第 11 节的明确 API；
- DatasetCatalog、FieldMetadata、RelationCatalog、QueryManifest；
- projection、filter、显式 registered join、stable ordering、lazy/batch series/event/array 读取；
- state/event/receipt lineage；
- proposed/validation/rejected diagnostic opt-in；
- PlotDataRequirements 检查与完整 PLOT_DATA_GAP_REQUEST 构造；
- 不隐式插值、滤波、平滑、峰值检测、重采样或修改 canonical 数据；
- Reader 包不得依赖 solver、surface evaluator、trial/commit physical APIs 或 plotting package。

G. schema 演化和 replay
- SemVer PATCH/MINOR/MAJOR 行为；
- additive、partial support、breaking rejection 和显式 migration lineage；
- 旧 bundle fixture、compatibility matrix 和 read-time adapter；
- BITWISE_REPLAY 与 SEMANTIC_REPLAY；
- ReplayManifest、差异 report、serial/parallel 和 codec/chunk invariance。

H. README 和人类输出介绍
- 在 M00 模块根目录 README.md 增加简短的“## 输出概览”；
- 说明核心 dataset、消费者、索引、单位/frame/reference、失败状态、ResultReader 最小示例及 DEV/VALIDATION 标签；
- 不复制完整 schema；
- 添加自动测试，验证 README 引用的 dataset/field ID 在 registry 中存在。

I. VALIDATION_ONLY demo
- 生成并读回冻结需求第 15.4 节的小 bundle；
- 包含两个 accepted points、一个 committed event、一个 rejected trial、一个 summary、一个 extension 和一个 chunked array；
- 打印简短输出概览或 catalog；
- demo 名称、字段和文档必须明确 VALIDATION_ONLY；
- 不得构造或暗示任何爪刺物理。

测试与验收：
- 完成冻结需求第 14–15 节的 unit/schema/compatibility/replay/fault-injection/performance tests；
- 测试必须可在干净环境用文档化命令运行；
- 性能报告记录硬件、OS、runtime、依赖、fixture 尺寸和各项指标；
- 测试报告不得只给单一 pass 布尔值；
- 运行 lint/type/schema/link 检查；
- 检查默认 ResultReader 查询绝不混入 rejected/proposed/validation 数据；
- 检查不同 chunk/compression 不改变 semantic hash；
- 检查每个故障注入点无部分 accepted 可见；
- 检查 M00 删除任何绘图依赖后仍完整，且一个仅依赖公开 Reader 的消费者可以读取 demo。

明确禁止：
- 编写求解器、物理事件或物理状态转换；
- 为“跑通”引入隐式单位、frame、reference point、参数默认或大刚度物理；
- 使用 float32、有损压缩或 NaN 作为 canonical missing；
- trial/rejected 值进入 accepted curve/event/summary/ranking；
- PROPOSED_SUPPLEMENT/VALIDATION_ONLY 提升为 accepted；
- M00 反向导入 M01–M08；
- M06 或任意消费者直接依赖 Parquet/Zarr 路径；
- 修改 theory accepted 文件或 archive；
- 自动启动 M01。

完成前：
1. 重新读取 git status --short；
2. 校验需求到实现/测试的追踪矩阵；
3. 校验文档链接、README 字段引用、schema/API signatures 和 SYSTEM 输出外壳；
4. 只精确暂存 M00 实现、测试、demo、README 和本窗口明确批准的关联文件；
5. 禁止 git add -A、git add .；
6. 使用 git diff --cached --name-only 与 git diff --cached --check；
7. 不提交、不格式化、不回退任何无关工作区改动；
8. 提交并推送前核对当前分支和 origin 可信目标；
9. 报告代码提交号、实际文件、测试结果、性能结果、demo bundle 路径和仍为 unavailable 的能力；
10. 停止，不得开始 M01。
~~~
