# B_INTEGRATION-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-16`  
> 正式 B 模型 SHA-256：`d64a387956b4d8b2317817c7429d1a57e594bab436fc5f1c9547126c95dd43ad`  
> 正式 B→C 合同 SHA-256：`fc9dd4504f1c6b0650361bbf289fdfdfc18ae1a01834887a3bf40bc09478c894`

## 产物、归档与运行身份

- 两个网页下载原件均按原文件名和原始字节保存到 `derivation/runs/B_INTEGRATION/raw_downloads/`；字节数与 SHA-256 已冻结到 `INPUT_MANIFEST.yaml`。
- 两个规范化候选与对应下载原件逐字节一致；`RAW_RESPONSE.md` 保存随附件收到的完整文本回答。
- 运行身份为 `B_INTEGRATION-r01`，实际目录为 `derivation/runs/B_INTEGRATION`，没有覆盖历史。冻结网页输入仍由提示词提交、逐文件字节数和 SHA-256 可复现。
- 候选公共合同含标记行块的 SHA-256 与网页声明的 `c4bfbdf...` 一致；身份转正后，正式模型和独立合同中的标记块仍逐字一致。

## 三个子模块的继承与一致性集成

- B1 的规则格点、针级身份/哈希、固定角/两种梯度、实际露出长度、球心共面、基座反算、共同 x/z 运动、刚性/独立弹簧拓扑、有向邻接与空间相关性均已保留。`2×5` 与 `5×2` 继续作为不同方向配置。
- B2 的全阵列 A embedded 调用、恒每单元 `P_z` 共同法向平衡、活动集、刚性 admissible graph、逐针 wrench 装配、raw/恒推力凝聚切线、共同最早事件和失败分类已统一。公共接口明确区分 `UX_PZ_BALANCED` 和 `PRESCRIBED_XZ_RESIDUAL`，便于 C 在不改写 B 机理的前提下选择内层平衡或规定姿态残量。
- B3 的事件前/事件点/后侧/最终候选四相试探、全阵列事件后重解、共享 DamageStore 冲突图与联合协调、同位置级联、自动重分配、释放/回弹/再挂接、100 mm 连续历史和幂等原子事务均已保留。
- 集成模型不是对 50 章上下文的摘要，而是将不可变配置、无副作用平衡试探和接受历史重构为单一残量—事件—事务链。

## 坐标、符号、单位、功、载荷与去重

- 公共 wrench 方向唯一为 A 对 B 的 `A_on_B`，在全局坐标、`O_A` 参考点表达。逐针参考点运输、C 层二次运输和 twist 变换保持标量功不变。
- mm、N、s、rad、N·mm、MPa 和 N/mm 为公共计算单位；针尖半径和弹簧刚度只在配置规范化时换算一次。
- `P_z/P_i` 只在 B 外层施加一次，不进入逐针 A 请求，不均分为 `P_i/N`。contact-only wrench、主动推力、x 控制反力和 y/转动约束反力严格分栏；C 的当前唯一外部接触装配策略为 `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1`。
- 球尖接触、三维摩擦、针梁、轴向弹簧、刚性 mount/硬限位、材料损伤和针体强度都有唯一所有者、状态量、力/位移和能量通道。B/C 只装配 A 净 wrench 一次，刚性 mount 不用大有限刚度伪装。
- B2 共同平衡已自动产生载荷共享，B3 事件后重分配是同一方程在新分支/损伤快照上的重解。不存在等载、邻居权重、距离权重或失效针旧峰值包。
- 功和能量账本单独记录 `R_x du_x-P_z du_z`、A 基座输入功、可恢复储能、摩擦/材料耗散、释放能和数值残量。同位置级联中 `du_x=0` 但 `du_z` 可非零，因此主动推力功未被漏计。

## 状态、事件、单步算法与下游合同

- 一个互斥单元主状态、针级正交子状态、独立事务 phase、原始连续量、同时事件组和级联组已闭合。接触释放、摩擦边界、真实滑移起始、支持迁移、材料起始/软化、针体强度、硬限位、碰撞、物理无解/失稳和数值失败未被压缩为同一 `failed`。
- 致命认证先处理合同/版本、未认证运动、域/几何/碰撞和模型/参数不可用；其余物理事件保留并发组，按“支持—粘滑/弹簧—容量—损伤—共同平衡”偏序重算。
- 可执行单步算法完整覆盖输入冻结、全阵列 A trial、法向 Newton/graph、共同事件定位、后侧重解、DamageStore 协调、级联 fixed point、功/质量/版本检查、prepare、commit、rollback 和 Zeno/状态哈希循环防护。
- standalone driver 只在单元验证边界推进 1 mm/s/100 mm 历史；C embedded trial 在四单元全局接受前无副作用。C 缩步或跨单元损伤变化后必须重调全部受影响单元，只能整体原子提交或全部回滚。
- `rocking=off` 可用当前 x/z 语义；`rocking=on` 的真实单元转动返回 `KINEMATIC_MODE_UNSUPPORTED/MODEL_UNAVAILABLE`。旋转旧 wrench、冻结旧姿态或投影运动都不能冒充支持。
- `B_TO_C_CONTRACT.md` 可独立阅读，冻结 C→B 输入、B→C 输出、参考点/单位/功共轭、作用点存在性、graph/切线有效域、事件归约、跨单元损伤、嵌套事务、完整回调条件和失败分类。

## 未决项、实现验证与工程事实

- 弹簧/主动推力离散点、砂纸目数、随机样本、材料/表面/摩擦/接触/损伤参数、CAD/制造误差、刚性 graph、数值容差/步长、能力特征、C 搜索准则/rocking 扩展、代码和实验均保留为未决项或明确关闭条件。
- 正式文件的 `accepted` 只表示 B 理论、数据和下游合同已通过当前语义审查；不表示求解器、CAD、材料参数、真实表面或实验已验证。
- `engineering_fixed_context 1.0.0` 保持不变；生成器仍应通过 9 个领域、48 条事实校验。本轮未固定任何未决值，也没有开始 C1/C2/C3 或全局集成。

## 可复现检查

- Markdown 代码围栏、显示/行内数学定界符和合同标记闭合；正式文件无模板占位符。
- 候选→接受版差异仅包含已记录的身份转正和对应时态文字，未改变方程、分支、数值、单位、范围或上下游语义。
- 数学回归覆盖全部正式阵列的格点计数/质心/包络、两种梯度的长度投影闭合、单位唯一换算、wrench 参考点运输的功不变性、恒推力凝聚切线、主动推力功方向、弹簧硬限位互补、事件最小分数和损伤冲突关系的顺序不变性。

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B_INTEGRATION/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B_INTEGRATION/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

三条命令均已通过。B 集成到此结束；实现、合同实现测试、参数标定、CAD、数值收敛和实验验证仍按正式模型中的关闭条件保持未决。
