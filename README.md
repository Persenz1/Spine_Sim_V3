# Spine Sim V3

面向钩爪式爬壁机器人爪刺啮合问题的三维准静态机理与求解器工程。

> 当前阶段分为理论与仿真器两条进度线。理论侧已完成网页端 `A1 → C3`、A/B/C 大模块集成和全局系统集成，归档的正式 1.0 文件仍是当前 `accepted` 规范；2026-07-17 的独立复核另形成 proposed 严格推导、入门教程和开发期参数策略，但尚未静默改写 accepted 1.0。仿真器侧已完成并验收 `M00 FOUNDATION`、`M01 SURFACE` 与 `M02 NUMERICS` 的软件范围；`M03 SINGLE_SPINE_REQUIREMENTS 1.0.0` 已冻结，M03 实现已交付。本征 artifact-backed standalone 路径已保存 5/5 个具有法向量的候选，并覆盖 fault rollback、idempotency 和 semantic replay；独立梯形 actuator 功积分与 14 类本征 runtime guards 也已实现。最终 medium 36 + gentle/sharp 2 已全部执行并形成明确 capability termination，但 0 个完成 100 mm、0 个 final M00 receipt、0 个趋势值；退化 `normal=None` 候选仍无法由冻结的 non-null schema 表示，真实平面功失配与完整事件/变形几何证据也仍阻断验收，因此当前状态是 blocked/evidence incomplete。M04–M07 未开始，M08 仍延期。`accepted` 机理、软件测试或解析 fixture 都不等于 A/B 物理、参数标定或实验验证已经完成。

## 1. 默认阅读入口

理论、论文、求解器和参数任务从 [`theory/README.md`](theory/README.md) 进入；仿真器规划、需求和实现任务从 [`docs/simulator_development/README.md`](docs/simulator_development/README.md) 进入，并按该模块要求补读理论交接文件。默认不要遍历 `archive/`：

1. 第一次学习：教学稿 → proposed 严格推导 → 独立复核报告；
2. 论文写作：proposed 严格推导 → 复核报告 → accepted 系统/模块模型作版本追溯；
3. 仿真器模块实现：仿真器开发入口 → 对应冻结需求/实施追踪 → 复核报告 → 开发策略与机器配置 → 对应 accepted 模型；
4. 审计 accepted 1.0：系统模型 → 对应 A/B/C 模块 → 必要接口；
5. 论文反向证据复核：`theory/evidence_reassessment/` 工作副本；查历史推导和原始运行时再进入 `archive/`。

proposed 严格稿不会自动覆盖 accepted 文件。遇到复核报告中的 P0 未闭合项时，只能采用已明确闭合的 M0 开发分支或返回不可用，不能直接把歧义公式写进求解器。

## 2. 当前目录结构

```text
Spine_Sim_V3/
├── README.md
├── pyproject.toml                  # Python 3.12 package、依赖和测试/lint 配置
├── src/spine_sim/
│   ├── foundation/                # 已实现并验收的 M00 基础包与 Result API
│   ├── surface/                   # 已实现并验收的 M01 表面/几何服务
│   ├── numerics/                  # 已实现并验收的 M02 数值/事件/事务/重放编排
│   └── single_spine/              # M03 A-M0 实现；验收证据尚未闭合
├── tests/
│   ├── foundation/                # M00 单元、schema、重放、故障和性能测试
│   ├── surface/                   # M01 契约、几何、重放、缓存和演示测试
│   ├── numerics/                  # M02 残量、事件、事务、重放、兼容和规模测试
│   ├── single_spine/              # M03 合同、几何、力学、事件、结果、campaign 和图证据测试
│   └── fixtures/                  # 兼容性与旧 bundle fixture
├── scripts/                       # M00–M03 验证、性能、campaign、兼容与验收辅助入口
├── reports/
│   ├── m00/                       # M00 Markdown 验收报告；机器产物本地重建
│   ├── m01/                       # M01 Markdown 验收/验证报告；机器产物本地重建
│   ├── m02/                       # M02 验证、性能、验收与机器可读摘要
│   └── m03/                       # M03 验证/性能/验收状态；当前不得标 ACCEPTED
├── docs/
│   ├── PROJECT_INSTRUCTION_MIGRATION_2026-07-18.md
│   └── simulator_development/
│       ├── README.md              # 当前模块门状态与开发入口
│       ├── requirements/          # 已冻结 M00–M03 需求
│       ├── implementation/        # M00–M03 实施追踪与验收证据入口
│       └── implementation_prompts/ # M00–M03 独立实现窗口提示词
├── theory/                         # 当前有效、供复核和论文化的机理文件
│   ├── README.md                   # 理论阅读地图与权威顺序
│   ├── paper/
│   │   ├── MECHANISM_DERIVATION_FORMAL.md
│   │   └── MECHANISM_DERIVATION_TUTORIAL.md
│   ├── review/
│   │   └── DERIVATION_VERIFICATION_2026-07-17.md
│   ├── implementation/
│   │   ├── BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md
│   │   └── DEV_BOOTSTRAP_PROFILE.yaml
│   ├── system/
│   │   └── SYSTEM_INTEGRATED_MODEL.md
│   ├── modules/
│   │   ├── A_INTEGRATED_MODEL.md
│   │   ├── B_INTEGRATED_MODEL.md
│   │   └── C_INTEGRATED_MODEL.md
│   ├── interfaces/
│   │   ├── A_TO_B_CONTRACT.md
│   │   └── B_TO_C_CONTRACT.md
│   └── evidence_reassessment/         # 论文反向工程事实/文献证据复核输入
│       ├── README.md
│       ├── engineering_fixed_context.md
│       └── literature/                # 29 组证据卡、审计 JSON 和关键图片
└── archive/
    └── web_pro_derivation_2026-07-17/  # 网页推导的完整审计与复现归档
        ├── README.md
        ├── docs/derivation_workflow/   # 指南、模板、窗口提示词
        ├── docs/extract/               # 模块规划、文献路由和 29 组完整提取源
        ├── engineering_fixed_context/  # 工程事实生成视图、YAML 源、schema 和生成器
        └── derivation/
            ├── prompts/                # 13 份正式网页执行提示词
            ├── runs/                   # 13 个运行目录及全部原始/验证产物
            └── modules/*/history/      # A1–C3 阶段快照
```

## 3. 当前理论文件的职责

| 位置 | 文件性质 | 后续用途 | 默认读取 |
|---|---|---|---|
| `theory/paper/` | proposed 严格推导与教学解释 | 论文方法稿、逐式检查、从牛顿力学过渡到算子表达 | 按任务 |
| `theory/review/` | 独立复核结论 | 识别 accepted 1.0 的闭合问题、实现阻断项和修订边界 | 编码前必读 |
| `theory/implementation/` | 开发期策略与机器配置 | 无完整壁面测量条件下启动仿真、参数分级与实验辨识 | 编码/标定必读 |
| `theory/system/` | A→B→C 全局集成规范 | 全局状态、变量、坐标、接口、事件、事务、统一算法、验证和实现交接 | 是 |
| `theory/modules/` | A/B/C 各层正式集成模型 | 单刺、阵列单元、十字对爪的层内方程与可执行细节 | 按需 |
| `theory/interfaces/` | 独立 A→B、B→C 合同 | 数据结构、作用方向、事务和禁止越界项的实现审计 | 按需 |
| `theory/evidence_reassessment/` | 工程事实汇总与 29 组文献提取材料 | 后续从论文和模型反向检查可补充内容 | 专项复核时 |
| `docs/simulator_development/` | M00–M08 模块规划与需求冻结流程 | 仿真器需求讨论、实现窗口生成和首版集成 | 开发任务入口 |

两份独立合同的正文已分别嵌入 A、B 集成模型；独立文件作为下游实现和审计入口保留。A3/B3/C3 最终滚动上下文已经被对应的 `INTEGRATED_MODEL 1.0.0` 取代，字节级相同的最终快照只保留在归档，不再与正式集成模型并列。

## 4. 归档产物的意义

完整分类和路径见 [`archive/web_pro_derivation_2026-07-17/README.md`](archive/web_pro_derivation_2026-07-17/README.md)。最重要的区分如下：

| 产物 | 意义 | 是否属于当前理论正文 |
|---|---|---|
| `PROMPT.md`、`derivation/prompts/` | 冻结网页任务边界、输入和输出合同 | 否 |
| `INPUT_MANIFEST.yaml` | 冻结 run_id、Git 输入提交、实际上传路径和 SHA-256 | 否 |
| `RAW_RESPONSE.md`、`raw_downloads/` | 网页端原始回答和下载原件，保持字节级审计性 | 否 |
| `*_CANDIDATE.*` | 从网页原件拆出的工作候选，供机械与语义审查 | 否 |
| `RUN_UPDATE_SUMMARY.yaml` | 子模块工程事实候选变化和模块变化摘要 | 否 |
| `CITATION_BRIEF.md` | 单轮关键公式与来源的旁路说明，不进入后续上下文 | 否 |
| `MECHANICAL_FIXES.md` | 无歧义格式、路径、状态和数学修复记录 | 否 |
| `VALIDATION_REPORT.md`、`validate_*.py` | 接受判定、回归检查和可复现验证脚本 | 否 |
| `modules/*/history/` | A1–C3 每阶段完整上下文快照 | 历史机理，不是当前规范 |
| `engineering_fixed_context/` | 工程事实生成视图、结构化 YAML 源、schema、manifest 和生成器 | 归档源保留；生成视图另复制到 `theory/evidence_reassessment/` 供反向复核 |
| `docs/extract/` | 模块计划、29 篇文献路由、ZIP、证据卡、审计 JSON 和图片 | 完整归档源保留；非 ZIP 材料另复制到 `theory/evidence_reassessment/literature/` |

## 5. 当前审查结论与关键限制

- 9 个子模块、3 个大模块集成和 1 个全局集成共 13 个运行目录均保留原始回答和验证报告；归档结论均为 `pass` 或 `pass / accepted`。该结论针对当轮产物、接口和解析构造，不等价于完整数学闭合、求解器回归、数值收敛或实验验证。
- A1–C3 的工程事实变化均为 `operation: none`，正式工程事实保持 `engineering_fixed_context 1.0.0`。
- A→B→C 的主坐标、力/矩、功共轭、contact-only wrench、分层调用和事务链经本轮复核总体一致。
- A 层仍需版本化修订有向量类型、损伤端点/剩余功、根映射和释放路径等 P0/P1 闭合问题；B 层必须以 A 的权威弹簧零分支为准，并沿曲线平衡路径定位事件，不能使用冲突摘要或直线插值替代。
- proposed 严格稿把 C 层拆成 `C-R`（共同参考位姿/共同径向坐标，论文与 M0 主线）和 `C-I`（独立 Z 执行器，仅在真实硬件具备该自由度时启用）。这个选择尚需通过版本化修订进入 accepted 模型。
- 当前 `B_TO_C 1.0.0` 只认证单元局部 x 与全局 Z 平移，不支持非零 `+X`、`45°` 偏心加载或 rocking 所需的局部 y、动态姿态和完整 twist。正式运行必须返回 `C_CONTRACT_EXTENSION_REQUIRED` 且零推进；这不是“零承载”或“物理失败”。
- 关闭该阻断需要版本化的 B 2.x 完整运动/姿态/6D graph 扩展及相应验证，不能用投影、旋转旧 wrench 或经验能力域绕过。
- 当前成熟度必须分层记录：M00 基础软件合同、M01 表面/几何服务与 M02 数值编排已实现并通过各自软件验收；M03 需求已冻结且代码已交付，但系统级验收证据不完整，不能标为 `ACCEPTED`；M04–M07 未开始，M08 仍延期。M03 的 `no_damage` 接触/梁/弹簧代码、单元测试和解析 fixture 不代表材料损伤、参数标定或实验验证已经完成，也不得提升任何 B/C 物理成熟度。

## 6. 项目物理主线

```text
表面查询
  → A：单刺连续搜索、接触、加载、滑移、损伤、脱离与再挂接
  → B：刚性/独立弹簧阵列的部分接触、共同平衡与失效重分配
  → C：十字对爪同步预紧、偏心平衡、渐进失效与最大承载
  → 原始连续仿真—实验输出
```

高层只能调用低层已经接受的接口，不得重新定义单刺接触、摩擦、材料强度、针级柔顺或阵列载荷共享。当前验证目标仍以参数趋势、方案排序和机理解释为主，不固定二元抓附成功阈值或综合评分。

## 7. 可立即启动的开发基线

在没有白光轮廓仪、目前只能做直线模组拖曳实验的条件下，编程不需要等待完整实验。M00 已提供严格配置、单位/身份、schema registry、事务、canonical bundle、`ResultWriter/ResultReader` 和重放基础；M01 已提供可重放的解析/合成表面、查询、球尖纯几何、tile/cache 物化及验证输出；M02 已提供 continuation、残量质量、signed events、event/post、原子事务、重放和诊断编排。M03 已按 [frozen 1.0.0 requirements](docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md) 交付 typed contracts、本征核、standalone 外层驱动、result extension、解析验证、campaign 编排和只读验证图。当前门是关闭 [M03 实施追踪](docs/simulator_development/implementation/M03_SINGLE_SPINE_TRACEABILITY.md) 中的验收 blocker，而不是开始 M04。仍需闭合的 M03 证据包括：

1. 真实本征核的 standalone 100 mm 基线，以及退化 `normal=None` 候选的可表示性与系统级 canonical persistence 闭合；
2. 修正真实力学/功模型，使已独立计算的梯形 actuator 输入功通过 closure，并补齐 return energy 累积及 step/event/LOD refinement；
3. 在现有 14 类本征 guards 与 standalone guards 之外，闭合冻结事件集合的 support migration、event/post 和路径级 replay 证据；
4. medium 36 distinct cases 加 gentle/sharp baseline 已整轮 streaming 执行并通过 capability-terminal pause/resume、serial/parallel slice 与 cold/warm 语义复核；仍需关闭事件/几何能力，使本征 baseline 完成 100 mm 并产生 final receipt 和趋势值；
5. 在已有真实 M01 局部极大/鞍点拒绝、解析平面 `Rt/8→Rt/10` witness 和终止行 replay 之外，补齐 rough/general refinement、最终变形几何重查询、previous-active lineage、弯曲体碰撞、full-kernel hard-stop 与 committed 100 mm replay。

`DEV_PRIOR` 参数只能用于宽范围扫描、灵敏度分析和代码回归，不能宣称为真实砖墙参数。现有拖曳实验优先辨识整机等效摩擦/阻力、峰值、稳态段、波动统计和速度依赖；单条总拉力曲线不能唯一反演表面 PSD、局部摩擦、针尖强度和损伤参数。

具体参数分级、可辨识性和升级门槛见 [`开发期标定与参数策略`](theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md)，机器可读默认值见 [`DEV_BOOTSTRAP_PROFILE.yaml`](theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml)。

## 8. 仿真器开发工作流

第一版仿真器的模块分配、无实验数据完整运行边界、需求讨论流程和逐模块窗口提示词见 [`docs/simulator_development/README.md`](docs/simulator_development/README.md)。

开发采用“一个模块需求讨论窗口 → 冻结需求和输出合同 → 另开实现窗口”的顺序。绘图模块是只读结果消费者，不参与仿真，也不能反向调用求解器；缺失的原始数据通过版本化数据缺口请求交回源模块处理。

当前门状态：

| 模块 | 需求状态 | 实现状态 | 当前入口 |
|---|---|---|---|
| M00 FOUNDATION | `1.0.0 frozen` | 已完成并通过验收 | [实施追踪](docs/simulator_development/implementation/M00_FOUNDATION_TRACEABILITY.md)、[验收报告](reports/m00/M00_ACCEPTANCE_REPORT.md) |
| M01 SURFACE | `1.0.0 frozen` | 已完成并通过验收（仅表面/几何） | [实施追踪](docs/simulator_development/implementation/M01_SURFACE_TRACEABILITY.md)、[验收报告](reports/m01/M01_ACCEPTANCE_REPORT.md)、[验证报告](reports/m01/M01_VALIDATION_REPORT.md)；性能 JSON 与演示图按文档命令在本地重建，默认不追踪 |
| M02 NUMERICS | `1.0.0 frozen` | 已完成并通过软件验收（不含 A/B 物理） | [实施追踪](docs/simulator_development/implementation/M02_NUMERICS_TRACEABILITY.md)、[验收报告](reports/m02/M02_ACCEPTANCE_REPORT.md)、[验证报告](reports/m02/M02_VALIDATION_REPORT.md)、[性能报告](reports/m02/M02_PERFORMANCE_REPORT.md)；大型 audit/bundle 按文档命令本地重建 |
| M03 SINGLE_SPINE | `1.0.0 frozen` | implementation delivered；acceptance blocked / evidence incomplete | [冻结需求](docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md)、[实施追踪](docs/simulator_development/implementation/M03_SINGLE_SPINE_TRACEABILITY.md)、[M03 报告入口](reports/m03/) |
| M04–M07 | 未冻结 | 未开始；M03 blocker 关闭前不自动推进 | [模块规划](docs/simulator_development/SIMULATOR_MODULE_PLAN.md) |
| M08 C DIAGNOSTIC | deferred | 未开始；不阻塞首版 A/B | [模块规划](docs/simulator_development/SIMULATOR_MODULE_PLAN.md) |
