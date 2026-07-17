# Spine Sim V3

面向钩爪式爬壁机器人爪刺啮合问题的三维准静态机理与求解器工程。

> 当前阶段：网页端 Pro 已完成 `A1 → C3`、A/B/C 大模块集成和全局系统集成，归档的正式 1.0 文件仍是当前 `accepted` 规范。2026-07-17 的独立复核另形成了 proposed 严格推导、入门教程和开发期参数策略；它们用于暴露并闭合编码前问题，但尚未静默改写 accepted 1.0。`accepted` 只表示当时的机理产物、接口和解析构造通过归档审查，不表示闭合修订已合入，也不表示求解器、数值收敛、参数标定或实验验证已经完成。

## 1. 默认阅读入口

所有当前任务先读 [`theory/README.md`](theory/README.md)，再按任务选择最短路径；默认不要遍历 `archive/`：

1. 第一次学习：教学稿 → proposed 严格推导 → 独立复核报告；
2. 论文写作：proposed 严格推导 → 复核报告 → accepted 系统/模块模型作版本追溯；
3. 求解器编码或参数工作：复核报告 → 开发策略 → 机器配置 → accepted 系统/模块模型；
4. 审计 accepted 1.0：系统模型 → 对应 A/B/C 模块 → 必要接口；
5. 查证据与历史：补充上下文 → `archive/` 中的原始回答、哈希、文献卡和验证记录。

proposed 严格稿不会自动覆盖 accepted 文件。遇到复核报告中的 P0 未闭合项时，只能采用已明确闭合的 M0 开发分支或返回不可用，不能直接把歧义公式写进求解器。

## 2. 当前目录结构

```text
Spine_Sim_V3/
├── README.md
├── AGENTS.md
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
│   └── supplements/
│       ├── A_MODULE_CONTEXT.md
│       ├── B_MODULE_CONTEXT.md
│       └── C_MODULE_CONTEXT.md
└── archive/
    └── web_pro_derivation_2026-07-17/  # 网页推导的完整审计与复现归档
        ├── README.md
        ├── docs/derivation_workflow/   # 指南、模板、窗口提示词
        ├── docs/extract/               # 模块规划、文献路由、证据包
        ├── engineering_fixed_context/  # 工程事实、YAML、生成器
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
| `theory/supplements/` | A3/B3/C3 后的最终完整滚动上下文 | 查找阶段证据、推导分支、迁移边界和被集成时压缩的说明 | 最后按需 |

两份独立合同的正文已分别嵌入 A、B 集成模型；没有接口审计需求时，不必重复阅读。三个补充上下文虽然也是 `accepted`，但已经被对应的 `INTEGRATED_MODEL 1.0.0` 取代，不能与正式集成模型并列为当前规范。

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
| `engineering_fixed_context/` | 坐标、尺寸、工况、开关、范围和未决参数的工程事实源 | 支撑权威，不是机理正文 |
| `docs/extract/` | 模块计划、29 篇文献路由、证据卡、图片和压缩包 | 证据支撑，不是机理正文 |

## 5. 当前审查结论与关键限制

- 9 个子模块、3 个大模块集成和 1 个全局集成共 13 个运行目录均保留原始回答和验证报告；归档结论均为 `pass` 或 `pass / accepted`。该结论针对当轮产物、接口和解析构造，不等价于完整数学闭合、求解器回归、数值收敛或实验验证。
- A1–C3 的工程事实变化均为 `operation: none`，正式工程事实保持 `engineering_fixed_context 1.0.0`。
- A→B→C 的主坐标、力/矩、功共轭、contact-only wrench、分层调用和事务链经本轮复核总体一致。
- A 层仍需版本化修订有向量类型、损伤端点/剩余功、根映射和释放路径等 P0/P1 闭合问题；B 层必须以 A 的权威弹簧零分支为准，并沿曲线平衡路径定位事件，不能使用冲突摘要或直线插值替代。
- proposed 严格稿把 C 层拆成 `C-R`（共同参考位姿/共同径向坐标，论文与 M0 主线）和 `C-I`（独立 Z 执行器，仅在真实硬件具备该自由度时启用）。这个选择尚需通过版本化修订进入 accepted 模型。
- 当前 `B_TO_C 1.0.0` 只认证单元局部 x 与全局 Z 平移，不支持非零 `+X`、`45°` 偏心加载或 rocking 所需的局部 y、动态姿态和完整 twist。正式运行必须返回 `C_CONTRACT_EXTENSION_REQUIRED` 且零推进；这不是“零承载”或“物理失败”。
- 关闭该阻断需要版本化的 B 2.x 完整运动/姿态/6D graph 扩展及相应验证，不能用投影、旋转旧 wrench 或经验能力域绕过。
- 当前成熟度应明确记录为：理论定义已形成，代码实现、数值验证、参数标定和实验验证均尚未完成。

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

在没有白光轮廓仪、目前只能做直线模组拖曳实验的条件下，编程不需要等待完整实验。M0 基线固定为：

1. 解析/合成表面与有限球尖几何；
2. 刚性 Signorini 法向接触与 Coulomb 摩擦；
3. Euler–Bernoulli 针体柔顺和 A 层权威弹簧图；
4. A/B 层平衡、活动集、事件定位和原子提交/回滚；
5. `no_damage` 作为首个连续回归分支，再逐步启用强度与损伤；
6. C 层先做 schema、拒绝路径、纯 Z/零载荷和径向扫描诊断；被合同阻断的工况保持 `Fcrit: null`。

`DEV_PRIOR` 参数只能用于宽范围扫描、灵敏度分析和代码回归，不能宣称为真实砖墙参数。现有拖曳实验优先辨识整机等效摩擦/阻力、峰值、稳态段、波动统计和速度依赖；单条总拉力曲线不能唯一反演表面 PSD、局部摩擦、针尖强度和损伤参数。

具体参数分级、可辨识性和升级门槛见 [`开发期标定与参数策略`](theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md)，机器可读默认值见 [`DEV_BOOTSTRAP_PROFILE.yaml`](theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml)。

## 8. 仿真器开发工作流

第一版仿真器的模块分配、无实验数据完整运行边界、需求讨论流程和逐模块窗口提示词见 [`docs/simulator_development/README.md`](docs/simulator_development/README.md)。

开发采用“一个模块需求讨论窗口 → 冻结需求和输出合同 → 另开实现窗口”的顺序。绘图模块是只读结果消费者，不参与仿真，也不能反向调用求解器；缺失的原始数据通过版本化数据缺口请求交回源模块处理。
