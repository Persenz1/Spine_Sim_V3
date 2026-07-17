# Theory 阅读与复核指南

本目录是当前唯一的理论工作区。后续“重新过目”和论文式重写应从这里开始；`archive/` 只承担追溯、复现和证据补查，不作为默认上下文。

## 1. 权威顺序

当文件之间表达粒度不同或存在看似冲突时，按以下顺序处理：

1. 归档中的正式工程事实约束高于所有机理文件；
2. [`system/SYSTEM_INTEGRATED_MODEL.md`](system/SYSTEM_INTEGRATED_MODEL.md) 是全局协调、状态、接口、事件、事务和实现交接的最高层规范；
3. A、B、C 的低层机理由各自 `INTEGRATED_MODEL 1.0.0 accepted` 拥有，系统层不得重新推导；
4. A→B、B→C 分别以 A、B 集成模型中的嵌入合同正文为权威；`interfaces/` 是便于单独实现和审计的等价副本；
5. `supplements/` 中的 `MODULE_CONTEXT 0.3.0 accepted` 是集成前详细基线，只用于补充追溯，不覆盖集成模型。

正式工程事实按需从 [`archive/web_pro_derivation_2026-07-17/engineering_fixed_context/engineering_fixed_context.md`](../archive/web_pro_derivation_2026-07-17/engineering_fixed_context/engineering_fixed_context.md) 查询。不要为了普通理论阅读预先加载整个事实库。

## 2. 最小阅读路径

### 全系统复核

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

- [`supplements/A_MODULE_CONTEXT.md`](supplements/A_MODULE_CONTEXT.md)
- [`supplements/B_MODULE_CONTEXT.md`](supplements/B_MODULE_CONTEXT.md)
- [`supplements/C_MODULE_CONTEXT.md`](supplements/C_MODULE_CONTEXT.md)

这些文件完整保留 A1–A3、B1–B3、C1–C3 的阶段推导、证据边界、备选分支、未决问题和交接记录。只有正式集成模型缺少所需细节时才读取相应章节；不要把整份补充上下文默认加入后续写作上下文。

## 3. 面向论文式重写的建议来源映射

| 拟写章节 | 首要来源 | 必要时追加 |
|---|---|---|
| 研究对象、范围、层级和假设 | 系统模型的规范身份、依赖链与边界章节 | 归档工程事实中的具体尺寸、工况和开关 |
| 表面与单刺连续啮合模型 | A 集成模型 | A 补充上下文中的证据与尺度迁移说明 |
| 多刺阵列共同平衡与重分配 | B 集成模型 | B 补充上下文中的阶段推导和构造验证 |
| 十字对爪预紧与偏心承载 | C 集成模型 | C 补充上下文中的合同覆盖证明 |
| 全局数值流程和状态机 | 系统模型的统一算法、事件和事务章节 | A/B/C 层内算法细节 |
| 参数、标定与证据边界 | 系统模型的未决问题和验证矩阵 | 归档 `CITATION_BRIEF`、文献路由和证据卡 |
| 验证方案与实验输出 | 系统模型的原始输出合同与全局验证矩阵 | 各集成模型的层内验证矩阵 |

正式论文稿应重新组织论证和符号，而不是直接拼接现有文件。重写时要区分“理论已定义”“代码已实现”“数值已验证”“实验已验证”四个等级，当前只能确认第一项。

## 4. 当前不能省略的限制

`B_TO_C 1.0.0 accepted` 尚未覆盖单元局部 y、真实转动、动态姿态或完整 SE(3) twist。因此：

- 同步预紧的 x/Z 路径可以按当前合同表达；
- 非零 `+X`、`45°` 偏心加载和 rocking 的理论方程已经定义，但当前合同不能在线执行；
- 正式调用必须返回 `C_CONTRACT_EXTENSION_REQUIRED` 并保持全部接受历史、损伤、事件、功、曲线和峰值零推进；
- 需要 B 2.x 的版本化完整运动接口、动态几何和 6D tangent/graph 及验证门槛后才能解除阻断。

后续复核时应优先检查这一接口缺口，以及所有未固定参数、模型开关和验证证据，不能把 `accepted` 误写成已完成求解器或已获得承载预测。
