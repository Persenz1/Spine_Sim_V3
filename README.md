# Spine Sim V3

面向钩爪式爬壁机器人爪刺啮合问题的三维准静态机理与求解器工程。

> 当前阶段：网页端 Pro 已完成 `A1 → C3`、A/B/C 大模块集成和全局系统集成。正式理论文件均为 `accepted`；这表示机理、接口和算法规范已通过当前审查，不表示求解器代码、参数标定、数值收敛或实验验证已经完成。

## 1. 默认阅读入口

后续复核或改写论文时，按下面顺序读取，默认不要遍历 `archive/`：

1. [`theory/README.md`](theory/README.md)：先看文件权威级别、阅读顺序和论文改写路线；
2. [`theory/system/SYSTEM_INTEGRATED_MODEL.md`](theory/system/SYSTEM_INTEGRATED_MODEL.md)：全系统唯一主模型，也是默认的首要理论输入；
3. 只在需要核对某一层细节时，读取 `theory/modules/` 中对应的 A、B 或 C 集成模型；
4. 只在接口实现或边界审计时，读取 `theory/interfaces/`；
5. 只在正式集成模型省略了阶段证据、备选分支或历史说明时，读取 `theory/supplements/`；
6. 只有需要追溯网页原文、输入哈希、候选稿、引用来源或验证过程时，才进入 `archive/`。

## 2. 当前目录结构

```text
Spine_Sim_V3/
├── README.md
├── AGENTS.md
├── theory/                         # 当前有效、供复核和论文化的机理文件
│   ├── README.md                   # 理论阅读地图与权威顺序
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

- 9 个子模块、3 个大模块集成和 1 个全局集成共 13 个运行目录均保留原始回答和验证报告；正式验证结论均为 `pass` 或 `pass / accepted`。
- A1–C3 的工程事实变化均为 `operation: none`，正式工程事实保持 `engineering_fixed_context 1.0.0`。
- A→B→C 的理论依赖、状态、事件、损伤、事务和输出规范已完成全局集成。
- 当前 `B_TO_C 1.0.0` 只认证单元局部 x 与全局 Z 平移，不支持非零 `+X`、`45°` 偏心加载或 rocking 所需的局部 y、动态姿态和完整 twist。正式运行必须返回 `C_CONTRACT_EXTENSION_REQUIRED` 且零推进；这不是“零承载”或“物理失败”。
- 关闭该阻断需要版本化的 B 2.x 完整运动/姿态/6D graph 扩展及相应验证，不能用投影、旋转旧 wrench 或经验能力域绕过。

## 6. 项目物理主线

```text
表面查询
  → A：单刺连续搜索、接触、加载、滑移、损伤、脱离与再挂接
  → B：刚性/独立弹簧阵列的部分接触、共同平衡与失效重分配
  → C：十字对爪同步预紧、偏心平衡、渐进失效与最大承载
  → 原始连续仿真—实验输出
```

高层只能调用低层已经接受的接口，不得重新定义单刺接触、摩擦、材料强度、针级柔顺或阵列载荷共享。当前验证目标仍以参数趋势、方案排序和机理解释为主，不固定二元抓附成功阈值或综合评分。
