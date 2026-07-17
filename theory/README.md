# Theory 阅读与复核指南

本目录是当前唯一的理论工作区。后续“重新过目”、论文式重写、仿真器理论交接和论文反向证据复核应从这里开始；`archive/` 保留完整源文件、历史推导和运行审计，不作为普通任务的默认上下文。

## 0. 本轮复核与开发入口（2026-07-17）

- [`paper/MECHANISM_DERIVATION_FORMAL.md`](paper/MECHANISM_DERIVATION_FORMAL.md)：`0.1.0-proposed`，可逐式审查的完整形式化推导；它给出建议闭合方式、适用条件和阻断边界，但不是 accepted 1.0 的静默替代品；
- [`paper/MECHANISM_DERIVATION_TUTORIAL.md`](paper/MECHANISM_DERIVATION_TUTORIAL.md)：教学解释稿，从牛顿平衡开始解释 wrench、残量、算子、互补接触、A/B/C 装配、事件和可辨识性；
- [`review/DERIVATION_VERIFICATION_2026-07-17.md`](review/DERIVATION_VERIFICATION_2026-07-17.md)：独立代数/物理复核；其中 P0/P1 是编码安全边界，不能因 accepted 标签而跳过；
- [`implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md`](implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md)：无白光轮廓仪、仅有直线拖曳实验时的开发期参数替代、实验辨识和分阶段决策；
- [`implementation/DEV_BOOTSTRAP_PROFILE.yaml`](implementation/DEV_BOOTSTRAP_PROFILE.yaml)：上述 M0 开发基线的机器可读配置，不代表真实壁面标定值；
- [`evidence_reassessment/`](evidence_reassessment/README.md)：工程事实汇总与 29 组文献提取材料，供后续从论文和模型反向检查可补充内容，不属于 accepted 理论正文。

这些新增文件不覆盖下文列出的正式权威模型。严格稿提出闭合修订，教程负责解释，复核报告记录问题，implementation 文件只负责开发期决策；只有经过版本化修订、审查和迁移后，accepted 模型本身才随之改变。

## 1. 权威顺序

当文件之间表达粒度不同或存在看似冲突时，按以下顺序处理：

1. 归档中的正式工程事实约束高于所有机理文件；
2. [`system/SYSTEM_INTEGRATED_MODEL.md`](system/SYSTEM_INTEGRATED_MODEL.md) 是全局协调、状态、接口、事件、事务和实现交接的最高层规范；
3. A、B、C 的低层机理由各自 `INTEGRATED_MODEL 1.0.0 accepted` 拥有，系统层不得重新推导；
4. A→B、B→C 分别以 A、B 集成模型中的嵌入合同正文为权威；`interfaces/` 是便于单独实现和审计的等价副本；
5. A3/B3/C3 的最终 `MODULE_CONTEXT 0.3.0 accepted` 是集成前历史基线，只保留在归档，不覆盖集成模型。

正式工程事实汇总按需从 [`evidence_reassessment/engineering_fixed_context.md`](evidence_reassessment/engineering_fixed_context.md) 查询；结构化 YAML 源、schema、manifest 和生成器仍保留在归档的 `engineering_fixed_context/internal/`。不要为了普通理论阅读预先加载整个事实库。

本轮 proposed 文件不在上述 accepted 权威链内；一旦与 accepted 1.0 冲突，必须明确标记“现行规范”和“建议修订”，不能混合拼接。实现任务也不能忽略已确认的 P0：在正式修订合入前，应采用复核报告和开发策略中已经闭合的 M0 分支，或对超出合同的功能返回不可用。

## 2. 最小阅读路径

### 第一次学习

按以下顺序：

1. [`教学稿`](paper/MECHANISM_DERIVATION_TUTORIAL.md)；
2. [`proposed 严格推导`](paper/MECHANISM_DERIVATION_FORMAL.md)；
3. [`独立复核报告`](review/DERIVATION_VERIFICATION_2026-07-17.md)。

这样先建立从牛顿力学到算子表达的直觉，再核对完整公式，最后区分哪些是 accepted 现状、哪些是建议闭合。

### 论文写作

先用 proposed 严格稿组织方法章节，再用复核报告标注假设、适用域和未闭合项；需要版本追溯时，回查 system 与 A/B/C accepted 模型。不要直接把 proposed 公式描述成已经进入 1.0 规范。

### 求解器编码与参数工作

依次读取：

1. [`独立复核报告`](review/DERIVATION_VERIFICATION_2026-07-17.md)；
2. [`开发期标定与参数策略`](implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md)；
3. [`M0 机器配置`](implementation/DEV_BOOTSTRAP_PROFILE.yaml)；
4. system 与实际实现层对应的 accepted 模块。

### accepted 1.0 全系统审计

只先读取 [`system/SYSTEM_INTEGRATED_MODEL.md`](system/SYSTEM_INTEGRATED_MODEL.md)。它已经包含：

- 表面→A→B→C→实验输出的完整依赖链；
- 全局状态、变量、坐标、单位、力和功方向；
- A→B、B→C 和 C→系统的接口映射；
- 统一试探、事件定位、损伤协调、级联、提交与回滚算法；
- 柔顺、载荷、损伤和耗散去重审计；
- 原始输出合同、验证矩阵、未决问题与实现交接。

### 层内深查

| 主题 | 读取文件 | 主要内容 |
|---|---|---|
| 随机表面与单刺 | [`modules/A_INTEGRATED_MODEL.md`](modules/A_INTEGRATED_MODEL.md) | 有限球尖几何、接触/摩擦、结构柔顺、材料与针体失效、释放和再挂接 |
| 阵列爪单元 | [`modules/B_INTEGRATED_MODEL.md`](modules/B_INTEGRATED_MODEL.md) | 阵列拓扑、共同平衡、活动集、载荷共享、事件后重分配和历史相关能力 |
| 十字主动对爪 | [`modules/C_INTEGRATED_MODEL.md`](modules/C_INTEGRATED_MODEL.md) | 同步搜索与预紧、六维装配、偏心加载、渐进失效、稳定分支和峰值 |

### 接口实现

- [`interfaces/A_TO_B_CONTRACT.md`](interfaces/A_TO_B_CONTRACT.md)：B 如何无副作用调用 A 单刺本征算子；
- [`interfaces/B_TO_C_CONTRACT.md`](interfaces/B_TO_C_CONTRACT.md)：C 如何调用 B 单元、装配 contact-only wrench、处理事件/损伤并完成原子事务。

合同正文已嵌入 A/B 集成模型。没有专门接口任务时，不要同时读取嵌入版和独立版。

### 证据或历史补查

- [`evidence_reassessment/README.md`](evidence_reassessment/README.md)：工程事实与 29 组文献证据的反向复核入口。
- [`A3 最终上下文`](../archive/web_pro_derivation_2026-07-17/derivation/modules/A/history/A_MODULE_CONTEXT_after_A3.md)
- [`B3 最终上下文`](../archive/web_pro_derivation_2026-07-17/derivation/modules/B/history/B_MODULE_CONTEXT_after_B3.md)
- [`C3 最终上下文`](../archive/web_pro_derivation_2026-07-17/derivation/modules/C/history/C_MODULE_CONTEXT_after_C3.md)

归档的三个最终上下文完整保留 A1–A3、B1–B3、C1–C3 的阶段推导、证据边界、备选分支、未决问题和交接记录；`evidence_reassessment/` 则提供工程事实和文献提取的理论工作副本。只有正式集成模型缺少所需细节或启动专项反向复核时才读取相应材料；不要把整份历史上下文或全部证据包默认加入后续写作上下文。

## 3. 面向论文式重写的建议来源映射

| 拟写章节 | 首要来源 | 必要时追加 |
|---|---|---|
| 研究对象、范围、层级和假设 | proposed 严格推导 | 系统模型的规范身份、依赖链与边界章节 |
| 表面与单刺连续啮合模型 | proposed 严格推导的 A 层 | A accepted 集成模型与归档 A3 最终上下文 |
| 多刺阵列共同平衡与重分配 | proposed 严格推导的 B 层 | B accepted 集成模型与归档 B3 最终上下文 |
| 十字对爪预紧与偏心承载 | proposed 严格推导的 C-R/C-I 边界 | C accepted 集成模型与合同覆盖证明 |
| 全局数值流程和状态机 | proposed 严格推导与复核报告 | 系统模型的统一算法、事件和事务章节 |
| 参数、标定与证据边界 | 开发期标定策略 | 系统未决问题、归档 `CITATION_BRIEF`、文献路由和证据卡 |
| 验证方案与实验输出 | 开发期标定策略与复核报告 | 系统及各模块验证矩阵 |

正式论文稿应重新组织论证和符号，而不是直接拼接现有文件。重写时要区分“理论已定义”“代码已实现”“数值已验证”“实验已验证”四个等级，当前只能确认第一项。

## 4. 当前不能省略的限制

除 `B_TO_C` 阻断外，本轮独立复核还确认：

- A 层的有向量类型、损伤端点/剩余功、根映射和释放路径需要版本化闭合；
- B 层重复的弹簧摘要不能覆盖 A 的权威零分支，事件定位必须沿 `(u_x,u_z(u_x))` 曲线平衡路径执行；
- proposed 论文主线采用共同参考位姿/共同径向坐标的 `C-R`；独立 Z 执行器的 `C-I` 只有在硬件确实提供相应自由度时才成立。二者不能混成一个残量系统。

`B_TO_C 1.0.0 accepted` 尚未覆盖单元局部 y、真实转动、动态姿态或完整 SE(3) twist。因此：

- 同步预紧的 x/Z 路径可以按当前合同表达；
- 非零 `+X`、`45°` 偏心加载和 rocking 的理论方程已经定义，但当前合同不能在线执行；
- 正式调用必须返回 `C_CONTRACT_EXTENSION_REQUIRED` 并保持全部接受历史、损伤、事件、功、曲线和峰值零推进；
- 需要 B 2.x 的版本化完整运动接口、动态几何和 6D tangent/graph 及验证门槛后才能解除阻断。

后续复核时应优先检查这些闭合问题、接口缺口、未固定参数、模型开关和验证证据，不能把 `accepted` 误写成已完成求解器或已获得承载预测。当前只确认理论定义与建议修订已经形成；代码实现、数值验证、参数标定和实验验证仍应分别记录。
