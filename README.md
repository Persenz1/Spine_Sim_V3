# Spine Sim V3

面向钩爪式爬壁机器人爪刺啮合问题的三维准静态机理与求解器工程。

> 当前阶段：工程事实和文献路由已完成规范化，正式机理推导与求解器实现将按照 A1 → C3 的物理依赖顺序推进。

## 1. 项目背景

本项目研究微小爪刺在红砖、混凝土和砂纸等粗糙表面上的搜索、接触、加载、滑移、局部失效、脱离与再挂接过程，并将单刺机理逐级扩展到规则多刺阵列和十字主动对爪。

目标不是复现某一次实验的偶然峰值，而是建立能够解释设计差异、支持结构选型并与实验趋势对比的自研三维准静态求解器。

主要研究内容包括：

- 比较不同爪单元设计及参数组合；
- 研究安装角、角度梯度、阵列尺寸与方向、针距、针径和针尖半径；
- 比较刚性阵列与独立轴向弹簧柔顺阵列；
- 选择合理的独立弹簧刚度范围；
- 预测不同设计的相对抓附能力和方案排序；
- 与直线模组拖拽实验比较趋势；
- 将爪单元模型扩展到偏心面内加载的十字主动对爪。

## 2. 验证原则

当前首要验证目标是：

- 参数变化方向与实验一致；
- 不同设计方案的排序大体一致；
- 模型能够解释刚性/柔顺阵列、阵列方向和安装角产生差异的原因。

现阶段不固定二元“抓附成功”阈值，也不固定综合评分。求解器必须优先保留力—位移、力—时间、法向位置、针级载荷、接触状态和事件历史等原始连续数据。

## 3. 物理架构

完整求解器遵循单向物理依赖：

```text
表面查询
  → 单刺连续啮合算子（A）
  → 阵列爪单元算子（B）
  → 十字主动对爪算子（C）
```

高层只能调用低层已经确定的物理接口，不得在阵列层或整爪层重新定义单刺摩擦、材料强度和针级柔顺。

### 3.1 大模块 A：随机表面到单刺连续啮合

| 子模块 | 任务 |
|---|---|
| A1 | 表面生成、有限针尖可达性与几何候选 |
| A2 | 单边接触、摩擦稳定与结构柔顺加载 |
| A3 | 滑移、局部材料失效、脱离与再挂接 |

A 模块最终形成可沿连续轨迹反复处理搜索、接触、加载、失效和再搜索的单刺算子。

### 3.2 大模块 B：刚性/独立弹簧阵列爪单元

| 子模块 | 任务 |
|---|---|
| B1 | 阵列几何、共同运动与柔顺拓扑 |
| B2 | 恒定法向主动推力下的活动接触集与载荷共享 |
| B3 | 失效重分配、连续再挂接与单元能力输出 |

B 模块必须显式产生部分接触、载荷不均、针级失效重分配和再挂接，不能用“有效刺数 × 平均单刺力”替代真实多接触平衡。

### 3.3 大模块 C：十字主动对爪同步预紧与偏心承载

| 子模块 | 任务 |
|---|---|
| C1 | 四单元同步搜索、内部预紧与停止条件 |
| C2 | 偏心外载、整体小角度摇摆与六维平衡 |
| C3 | 单元渐进失效、整体重分配与最大承载 |

C 模块调用 B 层单元响应，装配四个单元的整体合力、力矩、姿态和平衡，不重新推导针尖接触。

## 4. 模块间合同

### A → B

A 层向 B 层提供单刺状态、接触间隙与法向、接触力域、柔顺关系、失效和损伤状态、脱离/再挂接事件，以及给定基座位移后的单刺反力。

### B → C

B 层向 C 层提供单元合力与作用点、切线刚度或局部响应、内部状态、剩余行程、活动针集合、能力边界、失效/恢复事件，以及必要时回调完整针级求解的接口。

## 5. 仓库结构

```text
Spine_Sim_V3/
├── README.md
├── engineering_fixed_context/
│   ├── engineering_fixed_context.md
│   └── internal/
│       ├── facts/
│       ├── manifest.yaml
│       ├── schema.yaml
│       ├── build_context.py
│       ├── README.md
│       └── CHANGELOG.md
└── docs/
    └── extract/
        ├── ENGINEERING_FIXED_CONTEXT.md
        ├── MECHANISM_MODULE_PLAN.md
        ├── LITERATURE_MODULE_ROUTING.md
        └── 机理提取/
```

目录职责：

- [`engineering_fixed_context/engineering_fixed_context.md`](engineering_fixed_context/engineering_fixed_context.md)：当前完整、供人工审阅和网页上传的工程事实。
- [`engineering_fixed_context/internal/`](engineering_fixed_context/internal/)：工程事实的结构化 YAML、校验器、生成器和变更记录。
- [`docs/extract/MECHANISM_MODULE_PLAN.md`](docs/extract/MECHANISM_MODULE_PLAN.md)：A1–C3 的问题边界、理论交付和完成条件。
- [`docs/extract/LITERATURE_MODULE_ROUTING.md`](docs/extract/LITERATURE_MODULE_ROUTING.md)：29 篇文献到九个子模块的最小上传路由与备用规则。
- `docs/extract/机理提取/`：各文献的完整压缩包、证据卡、审计数据和关键图片。
- `docs/extract/ENGINEERING_FIXED_CONTEXT.md`：首次规范化迁移所使用的原始工程事实基线，仅作为来源存档。

## 6. 工程事实管理

工程事实与机理实现严格分离：

| 内容 | 存放位置 |
|---|---|
| 坐标、方向、尺寸、扫描集合、工况、模型开关、输出要求、未决参数 | `engineering_fixed_context` |
| 接触方程、摩擦稳定域、柔顺模型、状态机、损伤和重分配算法 | `RESULT` / `MODULE_CONTEXT` |
| 大模块向下游暴露的稳定接口 | `A_TO_B_CONTRACT` / `B_TO_C_CONTRACT` |

工程事实的结构化维护方向是：

```text
internal/facts/*.yaml
  → 结构与一致性校验
  → engineering_fixed_context.md
```

`engineering_fixed_context/` 中的完整 Markdown 是人工审阅入口；YAML 是后台结构化源。两者不得同时手工维护。

生成和检查命令：

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --write
```

## 7. 机理推导工作流

每个大模块按子模块顺序推进，并在三个子模块完成后进行一次独立集成：

```text
A1 → A2 → A3 → A 集成 → A_TO_B_CONTRACT
B1 → B2 → B3 → B 集成 → B_TO_C_CONTRACT
C1 → C2 → C3 → C 集成
                         ↓
                    A/B/C 全局审查
```

工作原则：

1. 网页端 Pro 模型负责基于最小文献包进行机理推导。
2. 当前大模块只维护一份滚动的 `MODULE_CONTEXT`；每个阶段保留本地版本快照，不额外维护重复的 `A1_RESULT/A2_RESULT/A3_RESULT`。
3. 每个大模块集成后形成 `INTEGRATED_MODEL` 和面向下游的合同。
4. 备用文献不默认上传，只有首选假设被证伪、存在证据冲突或需要专门标定分支时才追加。
5. Pro 对工程事实只能提出语义变更建议，不得自动覆盖正式基线。

## 8. 人工控制与变更审批

本工程以人工控制为最终决策门：

```text
Pro 提出推导或工程事实变更
  → Codex 检查语义、来源和实际 diff
  → 输出新增/修改/删除及影响说明
  → 人工确认关键变化
  → 更新 YAML 并重新生成完整 Markdown
```

以下变化必须显式说明，不能静默发生：

- 修改坐标系、方向或符号含义；
- 修改固定尺寸、参数范围或扫描集合；
- 修改运动自由度、加载工况或结构拓扑；
- 将未决参数改为固定值；
- 扩展首版明确排除的物理范围；
- 将某个机理推导结果提升为全局工程事实。

## 9. 当前范围边界

首版主线是高度场上的三维准静态针尖接触，同时保留完整三角网格能力分支。当前不包括显式裂纹扩展、碎屑动力学、针尖磨损、针杆或锥段分布承载、安装座/框架有限元、整机惯性动力学和大角度倾覆后运动。

完整数值、开关、工况和未决事项以 [`engineering_fixed_context.md`](engineering_fixed_context/engineering_fixed_context.md) 为准。
