# 25 — Time-dependent fiber bundles with local load sharing 反向审查

**文献身份与提取完整性：** Newman 与 Phoenix（2001），*Time-dependent fiber bundles with local load sharing*，DOI `10.1103/PhysRevE.63.021507`；对象是固定总载荷下一维随机寿命纤维束，不是微刺—粗糙壁面系统（`theory/evidence_reassessment/literature/25_time_dependent_fiber_bundles_local_load_sharing/evidence_card.md:5-17`）。提取审计覆盖全部 20 页、全部正文与附录，关键页 4、5、6、8、13、17 做了全分辨率复核（`theory/evidence_reassessment/literature/25_time_dependent_fiber_bundles_local_load_sharing/extraction_audit.json:1-32`）；Eq. (2.1)–(4.53)、(A1)–(A8) 均经视觉核对（`extraction_audit.json:34-106`），`uncertain_items=[]` 且状态为 `PASS_WITH_WARNINGS`（`extraction_audit.json:147-165`）。审计说明所有图的机理信息均可由已核公式和限定文字无损替代，故本卡无必须另看的图片（`extraction_audit.json:109-145,154-161`）。

**适用域：** 论文的直接结论建立在一维最近存活邻居等分、载荷守恒、固定总载荷、独立随机寿命和主要仿真取 `beta=1` 上；高载荷敏感区的闭式结果还偏重 `rho>>1` 与大 `N`。它不含球尖几何、摩擦、柔顺、位移控制、再挂接、多失效模式或实体材料标定（`evidence_card.md:21-74,225-232`）。因此，对“局部增载可诱发相关级联”和事件状态思想的置信度高；对项目采用论文公式、分区阈值或数值的证据不足。

下文短引 `evidence_card.md`、`extraction_audit.json`、`MECHANISM_DERIVATION_FORMAL.md`、`A_INTEGRATED_MODEL.md`、`B_INTEGRATED_MODEL.md` 和 `SYSTEM_INTEGRATED_MODEL.md` 分别指向本报告首段已列的第 25 卡目录，以及 `theory/paper/`、`theory/modules/`、`theory/system/` 中的同名仓库文件；所有数字均为 1-based 行号。

## 决定性判断（M1–M5）

| ID | 文献结论与本地证据 | 现行完整机理对应 | 分类 / 优先级 / 置信度 | 判断 |
|---|---|---|---|---|
| 25-01 | M1：失效单元载荷转给最近存活邻居，连续失效簇使尖端增载并形成正反馈（`evidence_card.md:21-30`）。 | FORMAL 规定针事件后切换分支、重解共同平衡得到载荷重分配（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1257-1276`）；accepted B 逐针保存事件前后 `Delta W_i`，恒 `P_z` 时检查总法向差量闭合（`theory/modules/B_INTEGRATED_MODEL.md:856-882`），复核确认该主链正确（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:278-312`）。 | `supported` / P1 / 高 | “局部失效—余针增/减载—可能继续触发事件”的方向已覆盖，而且现行力学重平衡比文献预设分配更适合本项目。文献只支持反馈现象，不支持特定转移权重。 |
| 25-02 | E1 给出一维内点簇尖端放大 `K_r=1+r/2`，要求左右最近邻等分和开边界单侧转移（`evidence_card.md:78-88`）。 | accepted B 明确失效针旧载荷不是按权重守恒的独立包（`B_INTEGRATED_MODEL.md:856-882`）；系统把单元内重分配归 B3，并禁止 C 使用固定转移矩阵或邻接权重（`theory/system/SYSTEM_INTEGRATED_MODEL.md:264-283`）。 | `insufficient_evidence` / P0 / 高 | 这是范围差异，不是真冲突；但若把 E1 或卡片所说“稀疏转移矩阵”（`evidence_card.md:216-223`）直接装入现行 B，就会成为真实合同冲突。最多可把 E1 当隔离的极简对照，不能替代每次全阵列重求。 |
| 25-03 | M2/E2：累计危险量 `integral kappa(load) dt` 首次达到随机名义寿命时失效，且 `kappa(l)=l^rho`（`evidence_card.md:32-41,90-106`）。 | FORMAL 的时间仅由拖曳位移映射，明确无速率本构时平衡不显式依赖速度（`MECHANISM_DERIVATION_FORMAL.md:153-173`）；当前 M0 为 `no_damage`，M1 是容量—局部化位移软化扩展（`MECHANISM_DERIVATION_FORMAL.md:78-103,889-1027`）。accepted A 同样以容量利用率和不可逆软化坐标演化，不含随机寿命危险率（`theory/modules/A_INTEGRATED_MODEL.md:898-969`）。 | `supplement_candidate` / P1 / 高（缺失判断）/低（目标适用） | 现行完整机理确实漏掉“在恒载下随时间自行失效”的可选物理。若持载/蠕变寿命是研究问题，可在 A 材料/针体所有者内新增版本化 `time_dependent_failure` adapter；没有目标微刺/基底持载试验时必须保持关闭。 |
| 25-04 | E3：分段常值增载后，投影剩余寿命按 `(old load/new load)^rho` 收缩；附录用逐单元存活、载荷和下一失效时刻做事件驱动求解（`evidence_card.md:108-118,209-218`）。 | 现行系统已具无副作用 trial、全局最早事件、回滚和原子提交（`SYSTEM_INTEGRATED_MODEL.md:1346-1537,1633-1650`），但其事件分数沿路径，A/B 时间只是 accepted 位移的派生量（`SYSTEM_INTEGRATED_MODEL.md:1192-1203,1923-1934`）。 | `supplement_candidate` / P1 / 高 | 事件架构可承载该扩展，但不能仅把寿命事件塞进现有路径分数。必须增加物理时钟/持载段、`hazard_integral` 和 `predicted_failure_time`，并规定 trial/rollback/commit；E3 只在采用 E2、幂律危险率且载荷分段常值时可用。 |
| 25-05 | M3：高载荷敏感性下，局部簇成核后可诱发脆性级联（`evidence_card.md:43-52,188-193`）。 | FORMAL 在事件后同一位置重求平衡，重分配若立即触发新事件则继续级联（`MECHANISM_DERIVATION_FORMAL.md:1862-1871`）；accepted B 每轮重求全部针、活动集、损伤与能量并显式防 Zeno（`B_INTEGRATED_MODEL.md:1167-1192`）。 | `supported` / P1 / 中高 | 级联的定性链一致；现行机理还允许接触、摩擦、材料、强度和再挂接耦合。文献没有验证这些项目分支，故不能用其 Monte Carlo 作为现行级联的物理验证。 |
| 25-06 | M3 同时强调：临界簇形成后仍需有限传播时间才整体破坏（`evidence_card.md:43-50`）。 | accepted B 规定事件定位、损伤协调和同位置级联不增加物理时间（`B_INTEGRATED_MODEL.md:1488-1498`）；系统输出合同也作同样规定（`SYSTEM_INTEGRATED_MODEL.md:1923-1934`）。 | `supplement_candidate` / P1 / 高 | 这是最重要的表面冲突：B 的“同位置级联”是准静态数值/物理闭合，不是论文的随机寿命传播。若启用时间危险率，应另有可推进时钟的 delayed cascade；不得把数值级联轮数解释成传播时间，也不得因此否定现行准静态规则。 |
| 25-07 | E4–E6/M3：一维弱区结构 `G_N≈1-exp[-N W(t)]`，高 `rho` 时寿命随规模降低并出现临界簇/对数尺寸效应（`evidence_card.md:120-158`）。 | 项目 B 只扫描 `2×2` 至 `6×6` 小阵列（`B_INTEGRATED_MODEL.md:96-111`）；现行验证要求逐步增加 surface realization/随机样本并检查统计稳定性，但没有弱区尺寸缩放测试（`SYSTEM_INTEGRATED_MODEL.md:2149-2165`）。 | `supplement_candidate` / P2 / 中 | 可补“阵列尺寸—失效簇—寿命/事件分布”敏感性和空间相关诊断；论文的大 `N` 一维渐近式不适用于至多 36 针、二维拓扑和再挂接系统，`W(t)` 必须由目标模型/试验重建。 |
| 25-08 | M4 的一般警示：总寿命/总承载统计相同，不代表空间失效模式或逐单元载荷谱相同（`evidence_card.md:54-63`）。 | accepted B 强制保存逐针状态、载荷、`N_eff`、CV/Gini、事件前后重分配和级联（`B_INTEGRATED_MODEL.md:1536-1609`）；系统亦要求总 wrench 与逐针原始量并存（`SYSTEM_INTEGRATED_MODEL.md:1936-1945`）。 | `supported` / P1 / 高 | 该关键结论没有被总量输出吞掉；现行输出合同已更严格落实。后处理仍不得以相同总曲线宣称相同局部机制。 |
| 25-09 | E7/M4：在 `rho=1,beta=1`、独立指数寿命与总载荷守恒下，LLS/ELS 整体寿命具有同一精确 Gamma 分布，但空间模式不同（`evidence_card.md:160-171,195-200`）。 | 当前验证矩阵有一针失效后全阵列重求、三轮同位置级联和随机样本稳定性测试（`SYSTEM_INTEGRATED_MODEL.md:2080-2116,2159-2165`），没有这一概率负面对照。 | `supplement_candidate` / P2 / 高 | 若实现可选危险率 adapter，可将 E7 加为严格单元测试：两种共享规则总寿命分布应一致而空间统计不同。这验证算法，不证明目标材料的 `rho=1` 或 `beta=1`。 |
| 25-10 | M5：`1/2<=rho<1` 近高斯，`0<rho<1/2` 受长寿命尾部主导，`rho=0` 时载荷共享不影响寿命（`evidence_card.md:65-74,202-207`）。 | 现行 A 的 `rho_k` 已被用作残余容量比（`A_INTEGRATED_MODEL.md:918-939`），且材料参数/模型尚待目标试验关闭（`A_INTEGRATED_MODEL.md:1805-1827`）。 | `insufficient_evidence` / P2 / 高 | 这些分区只属于该一维、`beta=1` 模型。不得作为微刺/红砖相图；若未来做灵敏度扫描，应另记 `rho_hazard`，避免与 accepted A 的残余容量 `rho_k` 符号碰撞，并报告为候选模型内结果。 |
| 25-11 | 论文固定总载荷、无外部柔顺、无再挂接；证据卡明确位移控制、有限阵列、柔顺和再挂接会改变级联（`evidence_card.md:49-50,225-232`）。 | 现行 B 同时支持恒 `P_z` 平衡和规定 x/z 残量，且接触释放、材料软化与再挂接均可继续演化（`B_INTEGRATED_MODEL.md:737-782,1056-1079,1121-1137`）。 | `insufficient_evidence` / P1 / 高 | 文献结果只可在现行恒 `P_z` 且关闭再挂接/额外柔顺的隔离分支中比较；对位移控制、C 预紧/偏心路径及恢复能力没有支持。属于控制域差异，不是真冲突。 |
| 25-12 | V4：双向指针和层次最小值搜索可把百万单元 LLS 仿真做到约 `O(N log N)`，并主张逐单元保存存活、载荷和投影寿命（`evidence_card.md:209-218`）。 | 现行 B 已有逐针 opaque 接受状态、完整事件记录、前后载荷和重放收据（`B_INTEGRATED_MODEL.md:1503-1568`），系统统一算法则要求每个事件点全量重调耦合平衡（`SYSTEM_INTEGRATED_MODEL.md:1447-1478,1531-1537`）。 | `supported` / P3 / 高（状态思想） | 状态/事件思想已覆盖；论文的指针数据结构、复杂度和运行时间不适用于二维几何查询、共同平衡、DamageStore 与再挂接。仅当新增隔离的 1D 回归 fixture 时才值得复用其算法。 |

## 真冲突与表面冲突

**真冲突：0 项。** 在相同对象、假设和控制域下，没有发现原文结论与 FORMAL 或 accepted 1.0 不兼容。现行机理没有宣称固定邻域等分，也没有宣称已覆盖随机持载寿命，因此“力学重平衡”与“LLS 规则”、“准静态同位置级联”与“有限时间传播”均是模型范围不同。

三类表面冲突必须显式隔离：一是 E1 的最近邻等分与 accepted B 禁止固定转移权重；前者只在论文一维束内成立。二是论文恒载下时间可自行推进，而现行 A/B 时间由位移映射；若研究持载破坏，这是缺模型，不是现行平衡式错误。三是论文 `beta=1` 无记忆寿命与项目不可逆 DamageStore/再挂接并存；前者只能作为新增竞争风险分支，不能覆盖现有材料、摩擦或恢复历史。

## 被漏掉的关键结论与 proposed 补充

1. **A 材料/强度层的条件时间危险率（P1）：** 新增显式模型身份 `time_dependent_failure`，保存每个针体/物理材料面片的累计危险量、随机名义寿命/分布版本、载荷通道、物理时钟和 seed。必须定义它与容量软化、针体强度、接触释放的竞争风险及“再挂接后是否继续累计”；目标持载/循环试验未标定 `rho_hazard,beta` 和时间尺度前返回 `MODEL_UNAVAILABLE`，不进入 M0。
2. **系统/B 的持载与时钟事件通道（P1）：** 在现有路径事件之外增加 `DWELL/HOLD` 协议和 time-domain earliest event；输出 `hazard_integral`、预测失效时刻、事件前后载荷及物理时间。trial、回滚和原子提交必须沿用现有事务不变量；同位置数值级联仍不计时，只有声明的物理持载/传播步推进时钟。
3. **时间模型的解析回归（P2）：** E3 用于分段常值增载更新测试，E7 用于 `rho_hazard=1,beta=1` 的 LLS/ELS 总寿命同分布负面对照；同时检查逐针空间聚簇不同。它们的身份只能是算法 fixture，不是目标参数证据。
4. **B/validation 的相关失效与尺寸诊断（P2）：** 从真实阵列几何与事件记录派生二维邻接图/机械影响图、簇大小、簇寿命、级联代数和边界位置，并扫描已允许的 `2×2`–`6×6` 与 surface realizations。邻接只作诊断；载荷仍由共同平衡重求。只有出现稳定的目标系统弱区缩放后，才可另拟 `W_project(t)`，不得复用 E4–E6。
5. **控制模式与恢复的分层对照（P2）：** 分别比较恒 `P_z`、规定 x/z、外部柔顺开关和再挂接开/关，明确哪些 LLS 趋势在目标系统仍保留。验证义务是同 seed/同 surface 的成对对照、事件/簇/寿命分布和不确定性；不能用论文单一固定载荷结果覆盖 C 路径。

## 不可直接移植

- 一维最近邻等分规则、开边界单侧转移以及 `K_r=1+r/2`；不得成为 B 的固定邻接矩阵或失效载荷包。
- `beta=1`、全部 `rho=0…20` 扫描点、`L=1`、无量纲时间尺度和独立指数名义寿命；均非微刺、钢针、红砖、混凝土或砂纸的实测参数（`evidence_card.md:173-184`）。
- E4–E6 的连续簇递推、`W(t)`、对数尺寸效应、`rho=2,N=4096` 约四分之一失效后崩塌、`rho=20` 的 `k*` 分段；仅适用于论文一维 LLS 与其有限尺寸区间（`evidence_card.md:120-158,180-184`）。
- `rho=1` Gamma 分布和 M5 的 `1/2` 分界只能作所声明概率模型的解析回归，不能作为项目材料相图或认证寿命。
- `N=8…2^20`、1024/262144 次重复、`O(N log N)` 与“百万单元少于一分钟”；它们是论文算法/硬件背景，不是当前耦合求解器性能要求（`evidence_card.md:180-184,209-214`）。
- 论文背景引用的岩石 Mode-I 指数 10–170，以及全部模型内 Monte Carlo 一致性；前者不是本文实测，后者不是实体微刺/壁面验证（`evidence_card.md:216-232`）。

## 优先级结论

- **P0：** 无需因本卡修改现行力学主链；必须继续禁止把 E1/固定转移矩阵接入 B，也不得用本文参数关闭现有材料缺口。
- **P1：** 若项目目标包含持载、蠕变或时间相关失效，时间危险率 adapter、物理时钟事件和竞争风险语义是现行“完整机理”的实质遗漏；对遗漏判断置信度高，对具体幂律适用性置信度低。
- **P2：** 增加 E3/E7 回归、二维相关失效/尺寸诊断和控制模式成对对照；它们先是验证义务和输出字段，不是 accepted 本构。
- **P3：** 附录指针/排序算法只保留为隔离 1D 大规模 fixture 的实现线索。

**总判定：** 第 25 卡未揭示现行 FORMAL/accepted 1.0 的真冲突；现行“事件后全阵列重平衡—同位置级联—逐针原始输出”已覆盖文献最重要的定性反馈，并比固定最近邻规则更适合本项目。真正漏掉的是可在恒载下随物理时间演化的随机寿命/危险率分支，以及由此产生的有限时间传播、寿命分布和尺寸诊断。该分支只能条件启用、独立标定并通过时钟事件与事务扩展接入，不能用论文的一维公式和数值直接补成目标系统定量机理。
