# 09 — Stochastic compliant spine arrays 反向审查

**审查对象：** Jiang, Wang & Cutkosky (2018), *Stochastic models of compliant spine arrays for rough surface grasping*，DOI 10.1177/0278364918778350。证据卡把对象限定为柔顺微刺单向/对置阵列的随机搜索、承载和二维拉离（`theory/evidence_reassessment/literature/09_stochastic_compliant_spine_arrays/evidence_card.md:3-16`）。提取审计覆盖全部 19 页、正文和附录 A–E（`extraction_audit.json:1-28`），状态为 `PASS_WITH_WARNINGS`（`extraction_audit.json:193-203`）；三张保留图已目视复核，其中 Fig. 8 是再挂接状态树、Fig. 12 是单阵列二维力域、Fig. 17 是预载相关对置安全域（`evidence_card.md:228-240`）。因此对论文所述趋势和模型结构的置信度高，但对目标红砖、现有十字机构和具体参数的可移植性仅中低。

## 决定性判断（M1–M6）

| ID | 文献结论与本地证据 | 现行完整机理对应 | 分类 / 优先级 / 置信度 | 判断 |
|---|---|---|---|---|
| 09-01 | M1：首次挂接是“立即命中点质量 + 指数搜索距离”的混合分布，依赖 Poisson、位置—强度独立假设（`evidence_card.md:20-29,101-111`）。 | FORMAL/A 已用显式三维 `SurfaceRealization`、有限球尖包络和全部合法支持候选取代标量凸体过程（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:316-371,373-454`；`theory/modules/A_INTEGRATED_MODEL.md:414-478`），但只把首次挂接分布列为实验标定对象（`MECHANISM_DERIVATION_FORMAL.md:2006-2078`）。 | `supplement_candidate` / P1 / 高 | 无冲突：一个是粗粒化统计基线，一个是 realization-resolved 主模型。应增加可选的两相首次挂接基准，用来检验显式三维表面 ensemble，而不能替代 A1 几何查询。
| 09-02 | M1 同时使用经验强度生存函数；低于 0.5 N 未可靠测量，3 N 以上右删失（`evidence_card.md:23-27,183-187`；`extraction_audit.json:44-47,193-197`）。 | FORMAL 明确标量拖曳不能唯一反演局部强度/损伤，并只拟合联合可观测量（`MECHANISM_DERIVATION_FORMAL.md:2031-2078`）；A 将表面强度保留为未决适配器（`theory/modules/A_INTEGRATED_MODEL.md:1882-1887`）。 | `supplement_candidate` / P1 / 中高 | 可补“删失感知的经验生存曲线”作为参数先验/验证输出；证据不足以把该论文的 `Pr(F)` 当作红砖材料本构或逐面片容量。
| 09-03 | M2：在论文趾—跟双点支承极限下，`tan(theta_m)=h_mis/d_unit`，短单元可筛掉不安全缓坡，但并非所有工况都更优（`evidence_card.md:31-40,88-99`）。 | 现行模型显式比较有限球冠支持、三维法向/摩擦和完整 wrench；B 扫描针距/阵列方向并保留真实基座偏置（`A_INTEGRATED_MODEL.md:449-478`；`theory/modules/B_INTEGRATED_MODEL.md:96-110,560-630`）。 | `supplement_candidate` / P2 / 中 | 不是冲突。该式仅可作为满足同一趾—跟几何时的解析 sanity check/设计解释，不能覆盖三维摩擦锥、体碰撞、材料或多支持 graph。
| 09-04 | M3 的物理链是挂接位置 → 剩余行程 → 单刺力/强度 → 阵列承载（`evidence_card.md:42-51,113-129`）。 | B 已逐针保存首次/再次挂接位置、弹簧余程、材料裕度和逐针 wrench，并保留事件前后变化（`B_INTEGRATED_MODEL.md:1536-1549,1593-1609`）。 | `supported` / P2 / 高 | 依赖关系已被更细粒度地包含；当前 `M0/no_damage` 只能支持几何—接触—柔顺部分，定量强度分支仍须按现有 unavailable 边界处理。
| 09-05 | M3 的期望剪应力积分假设独立刺、位移控制、位置—强度独立且无失效后换载（`evidence_card.md:45-51,126-129`）；作者警告忽略换载会高估能力、低估离散（`evidence_card.md:242-249`；`extraction_audit.json:193-196`）。 | B 的正式算子由共同 `u_z` 平衡决定非均匀载荷，事件后全阵列重求，禁止经验转移权重（`B_INTEGRATED_MODEL.md:739-782,832-882`）；独立复核确认该重平衡推导正确（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:278-312`）。 | `insufficient_evidence`（主求解器）；`supplement_candidate`（回归） / P1 / 高 | 看似冲突实为模型层级差异。不得把 Eq. (4)–(5) 接入正式承载算子；可保留“禁用重分配/IID”的降阶回归，验证正式求解器相对其能力下降和离散增大。
| 09-06 | M4：滑脱后重新搜索/挂接；未命中的后续层不再享有初始点质量（`evidence_card.md:53-62`；Fig. 8 说明见 `evidence_card.md:230-232`）。 | A/B 已有释放—可逆回位—继续同一路径—再挂接，路径、损伤和时间不重置（`A_INTEGRATED_MODEL.md:1369-1414,1559-1567`；`B_INTEGRATED_MODEL.md:1007-1016,1121-1136`）；系统已定义相应验证（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2093-2095`）。 | `supported` / P1 / 高 | 核心状态转移完整包含，且现行模型还增加显式载荷重分配、共享损伤和级联。论文 MDP 的点质量更新规则不应硬编码到显式几何路径。
| 09-07 | V2：再挂接对弱砂纸显著，对混凝土/瓦片的简化一次模型影响较小（`evidence_card.md:204-208`）。 | 现行状态机对所有表面统一启用再挂接，但验证矩阵尚无“按表面强弱关闭/开启再挂接”的消融；现有验证证据仍为 `BLOCKED_UNAVAILABLE`（`SYSTEM_INTEGRATED_MODEL.md:2082-2095`）。 | `supplement_candidate` / P1 / 高 | 这是被漏掉的关键经验结论：应增加 surface-stratified re-engagement ablation，比较整条曲线、峰值、方差和事件数，而非只检查状态机可达。
| 09-08 | M5：行程、刚度、阵列密度和强度存在条件化最优，不能推出“刺越多越好”（`evidence_card.md:64-73`）。 | B 已扫描阵列尺寸、针距、刚度和推力，保留完整曲线、平台、边际增益与逐针状态（`B_INTEGRATED_MODEL.md:96-111,1611-1636`）；C 停止门控也要求平台、增益、最弱和安全共同通过（`theory/modules/C_INTEGRATED_MODEL.md:1028-1139`）。 | `supported` / P2 / 高 | “条件化而非单调最优”的原则与现行机理一致；现行模型没有把论文最优点当固定答案，处理正确。
| 09-09 | 论文进一步给出“凸体越密，最优行程越短；最优 `F_max` 主要由强度分布控制”的趋势（`evidence_card.md:64-73,242-247`）。 | 现行验证只要求随机样本/设计排序稳定，并未把这两条趋势列成分层假设检验（`SYSTEM_INTEGRATED_MODEL.md:2149-2165`）。 | `supplement_candidate` / P2 / 中 | 可作为 DOE 先验和留出验证义务；只有在论文的占地—行程关系、独立刺和目标表面重新标定均成立时才预期复现，不能作为强制单调性。
| 09-10 | M6：两侧局部切向力相减、离面分量相加，预载相关安全域见 Fig. 17（`evidence_card.md:75-84,131-153,238-240`）。 | C 对四单元完整 wrench 求和，同时单列对置对的预紧与不平衡诊断；对称时全局面内力可抵消而径向驱动反力非零（`C_INTEGRATED_MODEL.md:956-1026`；`SYSTEM_INTEGRATED_MODEL.md:2122-2124`）。 | `supported` / P1 / 高 | 标量 Eq. (6)/(26) 已被坐标一致的 6D wrench 装配严格推广；无需另建第二套“切向减/法向加”力学。
| 09-11 | M6：增大内部预载通常增加法向能力但压缩净剪切余量；软弹簧+初力+硬止挡可形成近恒力策略（`evidence_card.md:75-83,192-193`）。 | C 保存 `p_X,p_Y,Delta_X,Delta_Y`、剩余方向能力、停止与安全裕度，但不预设该单调趋势（`C_INTEGRATED_MODEL.md:988-1026,1028-1139`）。 | `supplement_candidate` / P1 / 中高 | 建议新增“成对内部预载—残余方向能力—离散带”二维切片/回归；只作趋势验证，允许真实 3D 异质、损伤和力矩使趋势局部失效。
| 09-12 | 论文 E6 的硬件是中间弹簧与刺柔顺串联，参数为 `K_m,F_init` 和限位（`evidence_card.md:155-166,192-193`）。 | 项目固定为每单元 0.5–2 N 主动法向推力及共同径向搜索（`theory/evidence_reassessment/engineering_fixed_context.md:731-789,881-900`）；FORMAL 的 C-R 与 accepted C 的独立 `u_zi` 尚有 P0 边界分歧（`DERIVATION_VERIFICATION_2026-07-17.md:409-420`）。 | `insufficient_evidence` / P0 / 高 | 这是机构范围差异，不是真冲突。论文中间弹簧不能覆盖固定工程事实，也不能替项目解决 P0-SYS2；仅能作为未来另一个明确版本化机构的参考。
| 09-13 | 对置验证假设各向同性、两侧近同，只做二维，不含局部 y、左右异质和不均匀行力矩/失效换载（`evidence_card.md:81-83,251-258`；`extraction_audit.json:193-198`）。 | 现行 C 要求完整 wrench、异质 realization 和事件后全重平衡；当前 B 1.0 又明确不能执行非零 `+X/45°/rocking`（`C_INTEGRATED_MODEL.md:1374-1416`；`DERIVATION_VERIFICATION_2026-07-17.md:387-407`）。 | `insufficient_evidence` / P0 / 高 | 论文 V4/V5 不能验证或解锁项目的 3D 偏心承载，只能验证未来 2D、对称、固定姿态子问题。
| 09-14 | 提取审计发现 Eq. (29) 的自变量 `z` 与分母 `-x` 错配；二维再挂接高度修正也是经验闭合（`extraction_audit.json:128-131,176-190`）。 | 现行 A1 以几何查询和事件重求为权威，不需要该式（`A_INTEGRATED_MODEL.md:1504-1548`）。 | `insufficient_evidence` / P1 / 高 | 不得静默修正或实现 Eq. (29)，也不得把平均凸体高度线性修正升级为三维接触律；若作论文复现，必须单独重推并标明勘误假设。

## 真冲突与表面冲突

**真冲突：0 项。** 未发现现行机理在相同对象、假设和适用域下否定论文的实验结论。

表面冲突有三类：第一，论文 IID/无换载积分与 B 全阵列重平衡不同，但论文自身已把前者限定为简化并警告其偏差；第二，论文二维、镜像、忽略力矩的对置域小于项目 3D/异质/完整 wrench 域；第三，论文中间弹簧机构不同于项目固定主动推力和共同搜索机构。三者均是降阶或硬件范围差异。另有一项项目内部 P0：FORMAL C-R 与 accepted C 独立 `u_zi` 的预紧边界未统一；该论文既不造成也不能关闭该冲突。

## 被漏掉的关键结论与 proposed 补充

1. **A1/B 随机搜索基准（P1）：** 在 FORMAL 第 4/14/16 章或验证层增加 `mixed_first_engagement_baseline`，身份为可选统计模型/验证 fixture；输出 `alpha,lambda`、点质量、搜索生存曲线、拟合不确定度。须对目标红砖重新标定、按混合测度处理 `x=0`，并与显式三维 realization 的首次挂接分布做留出比较。
2. **A 材料先验（P1）：** 增加右删失感知的 `Pr(F)` 数据产品，身份为参数先验/观测模型，不是材料本构。必须保存测力下限、删失阈值、表面批次并与局部混合加载验证。
3. **B 再挂接消融（P1）：** 新增弱/强表面分层的 re-engagement-on/off 验证，比较均值、标准差、峰值、事件间隔和全路径功；验证义务是确认论文“弱表面更敏感”的方向，而非复现其数值。
4. **B 设计趋势（P2）：** 把“密度—行程”和“强度—单刺限力”的条件化趋势登记为 DOE 假设；同时保留背板不匹配、相关失效和显式载荷共享，若不复现则报告范围差异，不能强制调参迎合。
5. **C 对置二维回归（P1）：** 在合同支持的二维对称子域增加 Fig. 17 型安全域和 `preload versus residual shear margin` 输出；身份为解析回归/诊断切片，不是全局能力域，更不能绕过 B_TO_C 运动合同。

## 不可直接移植

- 三种论文表面的 `alpha,lambda,eta/Pr(F)`、约 10 μm 尖半径、1 mm 平均凸体高度，以及 0.5/3 N 测量截断（`evidence_card.md:183-191`）；均不能代表目标红砖或当前针批次。
- `N=20`、`d_unit=8 mm`、`d_stroke=1.5–8.5 mm`、`F_max=2–3 N`、二维法向限位，以及对置 `K_m=1 N/mm,F_init=6.6 N` 或 `0.5 N/mm,18 N`（`evidence_card.md:188-193`）。论文 stroke/中间弹簧不得与项目针级 4 mm 轴向弹簧或主动推力同名替换。
- Poisson、位置—强度独立、刺间独立、各向同性/两侧同分布、无 y/力矩/动态重分配等结论域（`evidence_card.md:251-258`）。
- 飞行器约 70% 成功率只是非受控系统演示，不能作为项目成功阈值或认证证据（`evidence_card.md:194,222-226`）。
- Eq. (29) 和经验二维再挂接修正，在完成独立重推与目标几何验证前均不可实现。

## 优先级结论

- **P0：** 不新增文献冲突修复；保持 C 预紧边界 P0-SYS2 与 B_TO_C 运动合同阻断，禁止借本论文中间弹簧或二维力域解锁正式 C 承载。
- **P1：** 增加两相首次挂接/删失强度基准、再挂接表面分层消融和对置二维安全域回归。兼容性判断置信度高，具体跨表面趋势置信度中高。
- **P2：** 将条件化最优作为 DOE 假设和解释性先验，不迁移最优数值。置信度中。
- **P3：** 软中间弹簧+初力+硬止挡只留作未来机构概念，不进入现行规范或参数包。

**总判定：** 现行完整机理没有与第09卡原始结论发生真冲突，并在显式三维支持、共同平衡、失效后重分配、共享损伤和级联上严格覆盖了论文简化模型的缺口。真正遗漏的是一组低成本、可审计的统计基线与验证义务，而不是新的主求解公式。
