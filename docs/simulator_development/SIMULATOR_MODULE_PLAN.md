# 第一版仿真器模块规划

**版本：** 0.1.1
**日期：** 2026-07-17
**产品定位：** 面向爪刺几何、阵列和柔顺参数的趋势分析与方案筛选工具

## 1. 规划决定

第一版不追求真实壁面的绝对承载预测，不等待白光轮廓仪或材料实验，也不反演不可辨识的微观参数。首版采用：

- 解析/程序化合成表面；
- 刚性 Signorini 单边接触与 Coulomb 摩擦宽扫描；
- Euler–Bernoulli 针梁；
- A 权威的刚性/独立轴向弹簧分支；
- `no_damage`；
- A/B 的连续准静态路径、活动集、事件定位、重平衡和事务；
- 公共随机数与宽先验下的排序稳定性。

正式 C 非零 `+X`、`45°`、rocking 和 `Fcrit` 受 `B_TO_C 1.0` 阻断，不得用投影或经验能力域绕过。因此首版完整实验以 A/B 设计筛选为闭环；C 只在首版后实现 schema、拒绝、纯 Z 和 prescribed-s 诊断。

### 1.1 理论交接边界

- 全局协调、状态、事件、事务和输出以 `theory/system/` 为权威；
- A/B/C 层内机理以 `theory/modules/` 为权威；
- A→B、B→C 的独立实现入口位于 `theory/interfaces/`，正文必须与模块内嵌合同保持逐字一致；
- P0/P1、安全开发分支和参数政策分别由 `theory/review/` 与 `theory/implementation/` 约束；
- `theory/evidence_reassessment/` 只提供工程事实/文献工作副本，不拥有本构或参数升级权；
- A3/B3/C3 滚动上下文只存在于归档，属于追溯材料，不得与集成模型并列实现。

## 2. “完整实验”的定义

一次首版完整实验必须：

1. 从一个版本化实验配置开始，不读取任何实测数据；
2. 解析全部固定参数、设计变量、不确定参数、数值参数和运行控制参数；
3. 生成带 ID、seed、hash、单位和质量信息的表面 realization；
4. 至少运行单刺连续拖曳和一个代表性阵列单元的 100 mm 连续拖曳；
5. 支持刚性安装与独立弹簧安装中的至少一组对照；
6. 保存 accepted 原始路径、逐针状态、事件、残量、事务和失败分类；
7. 生成按 case/design/seed 索引的摘要和排名输入，但不生成二元“抓附成功”；
8. 对所有未实现或不认证能力显式返回 `unavailable` 或规定错误码；
9. 可以由独立绘图进程仅通过结果 API 生成基线图；
10. 由运行 manifest 在相同代码、配置和 seed 下确定性重放。

smoke、development 和 screening 的具体设计矩阵与运行预算由 M05/M07 讨论窗口冻结。

## 3. 模块依赖图

```text
M00 foundation/result contracts
  ├──> M01 surface provider ──┐
  ├──> M02 numerical engine ─┼──> M03 single-spine A-M0
  │                          │          │
  │                          └──────────> M04 array B-M0
  └─────────────────────────────────────> M05 experiment runner
                                              │
                     canonical result API <───┤
                                              ├──> M06 plotting (read-only)
                                              └──> M07 first-release integration

M08 C diagnostic depends on M00/M02/M04, but is deferred and does not gate M07.
```

仿真模块不得依赖绘图模块。绘图模块可以在结果中发现数据缺口，但只能提出版本化输出变更请求，由数据所有者模块在自己的新窗口中修改。

## 4. 模块需求总表

### M00 — FOUNDATION：基础契约、配置与结果 API

**唯一职责**

- 冻结单位、坐标、ID、版本、错误分类和 provenance 外壳；
- 区分 immutable config、accepted physical state、trial cache、event、transaction 和 output；
- 定义配置解析/校验、resolved config、运行 manifest、结果 writer/reader 和 schema 演化；
- 允许各模块注册自己的字段和表，而不让 M00 拥有物理本构。

**必须讨论的参数**

- 配置分层和覆盖优先级；
- 单位输入与内部 N–mm–MPa 规范化；
- ID/hash/replay 规则；
- 结果存储格式、分块、压缩和精度；
- accepted、rejected trial、event、summary 的物理隔离；
- additive/breaking schema 版本规则。

**基础输出**

- run envelope、resolved config、source hashes、case index、状态与错误记录；
- accepted point/event/rejection 的公共字段；
- ResultReader API 和 schema 查询能力。

**图形职责**

无物理图。只需为所有下游图保留语义明确的字段、单位、frame、reference point 和 provenance。

### M01 — SURFACE：解析与合成表面提供者

**唯一职责**

- 平面、斜坡、正弦、单峰/坑、多峰和最近特征切换等解析表面；
- 无材料标签的 self-affine Gaussian 合成表面；
- 程序化/lazy tile 查询；
- 统一高度、点、法向、坡度、曲率/质量、邻域和碰撞查询。

**参数讨论重点**

- surface family、domain、seed；
- `H`、`Sq/Rt`、`lc/Rt`、各向异性与方向；
- 局部分辨率和精化；
- 表面 realization 的缓存、边界和可重复性。

**原始输出重点**

- realization 元数据与 hash；
- 查询质量、可信尺度和域状态；
- 可选的可视化采样网格，但不能让规则网格成为求解依赖。

**首批出图需求**

- 高度图和代表性剖面；
- 坡度/法向方向图；
- 高度与坡度分布；
- PSD/方向谱和分辨率收敛；
- 针尖尺度与表面尺度的无量纲对照。

### M02 — NUMERICS：延拓、事件、事务与重放

**唯一职责**

- 位移延拓、残量求解、活动集/graph 协调；
- signed event guard、括区和事件定位；
- 同位置同时事件/级联上限；
- trial/prepare/commit/rollback 和确定性重放；
- 数值失败、物理无解和认证拒绝的分离。

**参数讨论重点**

- 初始/最大/最小步长；
- 力残量、事件位置和互补容差；
- Newton/线搜索/括区迭代上限；
- 同位置级联与 Zeno 防护；
- accepted 与 trial 诊断保存粒度。

**原始输出重点**

- 每个 accepted 点的步长、残量、迭代、rank/branch/graph 质量；
- 事件函数、括区、定位误差、pre/event/post；
- rejected trial diagnostics 与 rollback 证据；
- replay/commit receipts。

**首批出图需求**

- 残量与迭代收敛；
- 步长随路径变化；
- 事件函数及括区放大；
- 步长/网格/容差精化误差；
- 失败分类统计。

### M03 — SINGLE_SPINE：A-M0 单刺算子

**唯一职责**

- 有限球尖可达/支持与非承载体碰撞；
- 刚性 Signorini/Coulomb；
- EB 梁和 A 权威安装弹簧图；
- 预载、100 mm 连续拖曳、粘着/滑动/释放/再搜索；
- `no_damage` 主线下的 contact-only wrench、状态和事件。

**参数讨论重点**

- `Rt,d,L,alpha,beta,E,nu,mu,Pz`；
- bending/mount 开关、弹簧刚度与 4 mm 行程；
- 表面引用、初始位姿、拖曳路径；
- 哪些是设计变量、宽先验、数值量或固定量。

**原始输出重点**

- 完整轨迹/时间、位姿、gap、支持、法向与切基；
- 接触力、`A_on_B` wrench、`Rx`；
- 梁/弹簧状态、残量、功和事件；
- 明确的 unavailable 损伤/强度字段。

**首批出图需求**

- `Rx-x`、`Rx-t`、`uz-x` 和力分量；
- 接触状态时间带与事件标记；
- 针尖/支持点局部几何；
- 梁挠度、弹簧压缩和余程；
- 残量、功误差和多峰记录。

### M04 — ARRAY_UNIT：B-M0 阵列单元

**唯一职责**

- 规则阵列、固定角/梯度角和长度补偿；
- 共同背板 `ux/uz` 与逐针 A embedded trial；
- `UX_PZ_BALANCED` 公共法向平衡；
- 部分接触、载荷不均、事件后重平衡和再挂接；
- 刚性与独立弹簧阵列比较。

**参数讨论重点**

- `nx,ny,spacing`、角度模式、针级广播；
- mount、spring stiffness、`Pz`；
- surface/seed 与共同随机数；
- 代表性对照与全扫描边界。

**原始输出重点**

- 单元六维 contact-only wrench、`Rx,ux,uz,Pz`；
- 每针 wrench、gap、状态、梁、弹簧和事件；
- `Nnominal,Ngeom,Nload,Neff` 与明确通道的不均载指标；
- 事件前后 `delta Wi`、重平衡残量和事务。

**首批出图需求**

- 单元力—位移/时间与法向位置；
- 逐针载荷热图/轨迹；
- 活动针数和 `Neff`；
- 弹簧压缩、余程和硬限位；
- 事件前后载荷重分配；
- 刚柔、转置阵列、角度、针距和预紧的趋势对比。

### M05 — EXPERIMENT_RUNNER：实验矩阵与批量执行

**唯一职责**

- 把参数空间变成可审计 case/design/seed 矩阵；
- smoke/development/screening 运行档；
- common random numbers、恢复、检查点、并发和失败隔离；
- 从原始结果计算版本化摘要与排序输入；
- 不拥有表面或 A/B 物理。

**参数讨论重点**

- 设计因素、对照组和分阶段扫描；
- seed 数、顺序加样与停止规则；
- case 预算、并发、缓存和重试；
- 摘要指标、置信区间与排名稳定规则。

**输出重点**

- experiment manifest、case table、resolved design matrix；
- 每个 case 的终态、结果引用和资源统计；
- 完整/失败/不可用的分栏；
- 峰值、多峰、正功、事件间距和排序用摘要。

**出图数据需求**

- 参数主效应与交互；
- 排名及置信区间；
- seed 收敛和排名翻转；
- 计算成本/失败域；
- 不同设计的分布而非单条漂亮曲线。

### M06 — PLOTTING：只读绘图与动态配方

**硬边界**

- 不导入求解器内部包；
- 不创建 trial、不推进 accepted state、不调用仿真；
- 不修改 canonical result bundle；
- 只通过版本化 ResultReader/API 和 schema 读取结果；
- 滤波、峰值检测、对齐和派生指标写入独立的 derived artifact，并记录版本与参数。

**讨论重点**

- 基线 plot recipes 与模块专属 recipes；
- 动态选择字段、筛选 case、分面、叠图和批量导出；
- 图片格式、尺寸、主题、论文/调试模式；
- 大结果的按需读取和缓存；
- 缺字段时怎样生成 `PLOT_DATA_GAP_REQUEST`。

**输出**

- figure files；
- plot manifest；
- 可重现的 recipe/config；
- derived tables/cache；
- 数据缺口请求，不得直接修改源模块。

### M07 — FIRST_RELEASE_INTEGRATION：首版完整实验

**唯一职责**

- 集成 M00–M05，不在这里发明新物理；
- 冻结一个小而完整的首版无实验数据基准矩阵；
- 从干净环境用一个文档化入口跑完并生成结果；
- 另行调用 M06 读取结果，证明绘图与仿真单向解耦；
- 形成回归证据和用户运行说明。

**必须验收**

- 解析回归、单刺、代表性 B 阵列、刚柔对照和多个 seed；
- 100 mm accepted 路径不因释放而重置；
- 完整 raw/event/summary/manifest；
- 可重放、可恢复、失败分类完整；
- 所有结果有 `not_certifiable` 标签；
- 仿真删除绘图依赖后仍能独立运行，绘图删除求解器依赖后仍能读取既有结果。

### M08 — C_DIAGNOSTIC：延期的 C 合同安全诊断

**定位**

首版完成后再讨论，不阻塞 A/B 参数选型工具。

**当前只允许**

- request/response schema；
- B→C coverage audit；
- zero increment、pure Z、conditional x/z preload trial；
- C-R prescribed-s scan，不自动锁定；
- 解析 mock，强制 `not_certifiable/not_comparable`；
- 非零 `+X`、`45°`、rocking 的 `C_CONTRACT_EXTENSION_REQUIRED` 零推进记录。

**出图需求**

- 四单元响应随 `s` 的诊断图；
- 内预紧/最弱分支原始特征；
- guard/coverage 状态；
- 拒绝原因与不支持 twist 分量。

不得输出正式 `Fcrit`，不得把解析 mock 加入 A/B 设计排序。

## 5. 参数所有权规则

每个需求文件必须把参数分成五类：

1. `FIXED_ENGINEERING`：正式工程事实，不得静默修改；
2. `DESIGN_VARIABLE`：用于选型的离散或连续因素；
3. `DEV_PRIOR_UNCERTAINTY`：宽扫描，不解释为真实材料值；
4. `NUMERICAL_CONFIGURATION`：靠收敛确定；
5. `RUN_AND_PLOT_CONFIGURATION`：只影响执行或展示，不改变物理。

任何 `unavailable/unresolved` 项必须保留字段和原因，不能用默认值悄悄补齐。

## 6. 输出与绘图协作规则

各物理模块负责保存语义完整的 canonical raw output；实验模块负责索引和摘要；绘图模块负责派生与展示。若绘图需求缺数据：

1. 能由现有 raw 字段无歧义推导：在绘图侧形成版本化 derived field；
2. 需要新的原始物理状态：生成数据缺口请求；
3. 数据所有者模块在新的需求/实现窗口中审查并增加输出；
4. schema 做版本化迁移；
5. 旧结果仍可由旧 reader 或明确的不兼容错误处理。

绘图需求不得成为求解器内部的反向依赖。
