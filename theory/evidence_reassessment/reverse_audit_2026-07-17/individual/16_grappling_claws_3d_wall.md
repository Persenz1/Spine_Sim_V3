# 16 — grappling claws 3D wall 反向审查

**状态：** non-normative reverse-audit working material
**审查对象：** Xu et al. (2020) 三维粗糙墙有限钩尖可达性—摩擦自锁—十字主动爪抗振证据卡
**结论摘要：** 未发现同对象、同假设、同适用域下的真冲突。M1 的三维表面输入与尺度质控、M2 的局部法向—载荷—摩擦关系、M3 的有限球尖可达性、M6 的事件后重平衡/渐进脱离均已被现行机理覆盖，而且 FORMAL/A 的三维有符号距离、合法球冠和 SOC Coulomb 锥比论文的离散空球与二维角判据更一般。主要遗漏是：把扫描/配准/插值误差显式绑定到尖端尺度的验收字段、一个用于回归的离散空球参考后端、纵横对爪功能贡献诊断、主动驱动撤除的边界事件，以及几何预测—真实接触的点级留出验证。论文的候选计数、特定脱离顺序和振动阈值只能作趋势证据，不能成为成功概率、通用动力学规律或本项目参数。

## 1. 身份、提取完整性与适用域

- 文献为 *Grappling claws for a robot to climb rough wall surfaces: Mechanical design, grasping algorithm, and experiments*，DOI `10.1016/j.robot.2020.103501`；对象是有限半径钩尖在三维点云上的接触/摩擦筛选及十字主动爪原型，见 `theory/evidence_reassessment/literature/16_grappling_claws_3d_wall/evidence_card.md:3-12`。
- 提取审计覆盖全部 15 页、所有机理/实验章节，并对公式、表格和三个保留图做高分辨率复核，最终状态 `PASS_WITH_WARNINGS`；见 `theory/evidence_reassessment/literature/16_grappling_claws_3d_wall/extraction_audit.json:12-35`、`:205-216`。本审查另目检 Fig. 5、12、20；卡片锚点分别为 `evidence_card.md:184-196`，确认二维受力符号、半径/角度候选图与非同步标记位移。
- 适用域分为三段且不可混成一条已验证链：砂石墙扫描/插值、离散点云几何仿真、磨石墙单原型振动试验；卡片明确三者不是同一受控红砖数据链，见 `evidence_card.md:207-214`。论文单钩判据是二维刚性准静态，振动部分则无重复数、误差带、接触力和可迁移动力学模型，见 `evidence_card.md:32-41`、`:76-85`。
- FORMAL 是 `0.1.0-proposed`，不覆盖 accepted 1.0；其主模型是三维准静态有限球尖—阵列—十字系统，且当前 C 非零偏心/rocking 仍被合同阻断，见 `theory/paper/MECHANISM_DERIVATION_FORMAL.md:1-15`。

## 2. 逐项结论表

| # | 文献原结论与本地来源 | 现行机理对应位置 | 分类 | 判定、优先级与置信度 |
|---:|---|---|---|---|
| 1 | M1：扫描、拼接、滤波形成三维表面，形貌、尖端尺度与搜索方向共同进入候选判别；`evidence_card.md:21-30`。 | accepted A 的 `SurfaceRealization` 已保存坐标、有效域、质量掩膜、可信波数带、测量/生成元数据和不确定性；`theory/modules/A_INTEGRATED_MODEL.md:414-428`。 | `supported` | 数据接口与适用域一致；文献支持“实测表面进入 A1”，不支持沿用其砂石墙。P2，高置信度。 |
| 2 | 扫描误差约 59/19 µm，却用 4 µm 插值和 10 µm 尖端，微尺度位置未获分辨率保证；`evidence_card.md:150-152`、`:207-210`，审计 `extraction_audit.json:168-173`。 | A/系统已有可信带不足即 `GEOMETRY_UNCERTAIN` 和 MTF/SNR、多分辨率关闭条件；`theory/modules/A_INTEGRATED_MODEL.md:1796-1799`、`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198`。 | `supplement_candidate` | 机理方向已支持，但 schema 尚可显式增加配准残差、原生点距、插值点距、可信最短波长与尖端半径比，并禁止插值扩张可信带。P1，高置信度。 |
| 3 | M2/E1：二维点接触中局部法向、载荷方向和 \(\mu\) 决定自锁，\(\alpha<\theta+\arctan\mu\)；`evidence_card.md:32-41`、`:89-101`。 | FORMAL 用每个支持的三维 SOC Coulomb 互补和最大耗散统一粘/滑；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:546-606`，verification 已确认该骨架，`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:170-182`。 | `supported` | 现行式是论文二维判据的三维推广，不是真冲突；可把 E1 加成平面单支持退化回归，但不能替代 SOC。P2，高置信度。 |
| 4 | E3 的 \(\theta_{min}\) 与 E1 的力方向角复用符号，且论文未推导 \(\theta_{min}(\mu,\text{load})\)；`evidence_card.md:127-144`，审计 `extraction_audit.json:174-178`。 | A 把几何候选与摩擦可行分层，并保留最终挂接判据未决；`theory/modules/A_INTEGRATED_MODEL.md:478`、`:1877-1878`。 | `insufficient_evidence` | 禁止把 \(40^\circ/50^\circ\) 直接映射为本项目 \(\mu\) 或成功阈值。若需快速筛选，只能注册独立、可校准的几何阈值模型。P1，高置信度。 |
| 5 | M3/E2：半径 \(r\) 的空球、三点边长/面积和球内无其他点过滤有限尖端不可达组合；`evidence_card.md:43-52`、`:103-125`。 | FORMAL 以有符号距离球包络、合法球冠、二阶最小条件和面—边—顶点全候选比较实现同一非穿透目的；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:341-454`。 | `supported` | 离散空球与连续/网格最近特征是表示差异；后者更一般。verification 的 P1-A6 也要求空球/全候选/邻域枚举，`DERIVATION_VERIFICATION_2026-07-17.md:265-271`。P1，高置信度。 |
| 6 | 论文给出可复现的离散空球算法链，但只演示 1176/1436 点且有非局部组合风险；`evidence_card.md:103-125`、`:209-210`。 | A 的几何验证要求窄槽、多支持及高度场—网格加密一致，FORMAL 要求表面分辨率收敛；`theory/modules/A_INTEGRATED_MODEL.md:1741-1744`、`theory/paper/MECHANISM_DERIVATION_FORMAL.md:2113-2120`。 | `supplement_candidate` | 增加只用于验证的 `POINT_CLOUD_EMPTY_SPHERE_XU2020` oracle，与 SDF/网格后端比较候选集合、假阴性和网格收敛；不得成为唯一生产算法。P2，中高置信度。 |
| 7 | M4/V1：在三组点云上，减小 \(r\) 或 \(\theta_{min}\) 增加候选计数；`evidence_card.md:54-63`、`:163-168`。 | 现行机理显式保留有限尖端半径，但没有宣称候选数对半径普遍单调；A 还同时检查球冠合法性、体碰撞、摩擦和材料安全，`theory/modules/A_INTEGRATED_MODEL.md:449-508`。 | `insufficient_evidence` | 可作为同点云、同算法的方向回归；不能提升为普遍定理，因为真实尖端强度、磨损、非球形和表面尺度会改变排序。P2，高置信度。 |
| 8 | 候选三角形重叠，计数不是唯一接触数、面积、概率或承载力；`evidence_card.md:57-63`、`:198-205`，审计 `extraction_audit.json:180-182`、`:205-207`。 | A 明定 `candidate_any/robust` 只是几何必要标签；B 禁止从相关性产生 IID 成功率或载荷转移权重；`theory/modules/A_INTEGRATED_MODEL.md:466-478`、`theory/modules/B_INTEGRATED_MODEL.md:684-690`。 | `supported` | 现行机理已正确避免“候选计数→抓附成功/承载热力图”的误推。P1，高置信度。 |
| 9 | M5：纵向副爪主抓持、横向副爪抑制侧滑/翻转，主动气缸搜索/夹紧；`evidence_card.md:65-74`。 | C 已保留对置组预紧、差值和完整 contact-only wrench，且六维平衡不冻结横向组贡献；`theory/modules/C_INTEGRATED_MODEL.md:988-1016`、`:2311-2321`。 | `supplement_candidate` | 建议增加 `pair_role_diagnostics`：两对单元对目标力、侧向力和 X/Y 力矩的逐项贡献；“纵向主、横向辅”只能是给定加载/姿态下的观测标签，不应硬编码。P2，中高置信度。 |
| 10 | M5 还称弹性钢片补偿墙面不平，但未给钢片刚度、传力或逐钩载荷；`evidence_card.md:68-74`。 | 现行系统把十字定义为无质量刚体且禁止新增框架/连接件柔顺；`theory/system/SYSTEM_INTEGRATED_MODEL.md:1771`，accepted C 也排除框架/传动链柔性，`theory/modules/C_INTEGRATED_MODEL.md:82-91`。 | `insufficient_evidence` | 这是不同原型/边界的范围差异，不是真冲突。只有本项目 CAD 确有该柔顺且完成独立标定时，才可另立 C 结构柔顺候选；本文不能给参数。P2，高置信度。 |
| 11 | M6/V2：主动驱动开时，同频纵/竖向振动可承受更大幅值；`evidence_card.md:76-85`、`:170-175`。 | FORMAL/C 有同步预紧与事件重平衡，但真实执行器端点/功尚 unavailable，且模型准静态、不含惯性；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1480-1529`、`theory/modules/C_INTEGRATED_MODEL.md:82-91`。 | `supplement_candidate` | 增加版本化 `actuation_state` 与“已预紧→驱动撤除”的边界切换试验/输出；当前只能验证主动预紧提高准静态扰动裕度的方向，不能复现 12 Hz 阈值。P1，中高置信度。 |
| 12 | M6/V3：撤去驱动后各标记位移非同步增长，说明整体失效不是单阈值；`evidence_card.md:177-196`。 | FORMAL 在事件后同位置重求并处理重分配级联；C 要求首峰/首针失效后继续至稳定分支穷尽，`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1771-1869`、`theory/modules/C_INTEGRATED_MODEL.md:2273-2295`。 | `supported` | “局部先后脱离、继续重平衡”已充分覆盖；可把事件序列、每单元状态和再挂接作为对照输出。P1，高置信度。 |
| 13 | 作者据标记轨迹推断右爪先脱离、再左/下、最后上爪；但单原型、无重复/力测量，`evidence_card.md:76-84`、`:177-182`，审计 `extraction_audit.json:205-211`。 | System 只要求保存首针/单元、峰后渐进脱附和可恢复/不可恢复分支，不预设单元次序；`theory/system/SYSTEM_INTEGRATED_MODEL.md:2140-2146`。 | `insufficient_evidence` | 特定顺序只可作为该试验 replay 的定性观察，不得成为通用事件优先级、横纵分载规则或验证硬断言。P3，中等置信度。 |

## 3. 真冲突与表面冲突

**真冲突：0 项。** 四处表面不一致均可由适用域解释：

1. 论文的“三点空球”与现行 SDF/网格最近特征是离散数据算法和连续几何后端的差异；二者都执行有限球非穿透，且 FORMAL 已补全二阶最小与全候选认证。
2. 论文二维角度自锁与现行三维 SOC 摩擦锥是特例与推广的关系；只有错误地把 \(\theta_{min}\) 当作由 \(\mu\) 唯一决定时才会制造伪冲突。
3. 论文原型的弹性钢片与本项目刚性十字不是同一物理对象；工程固定边界优先，不能用该论文静默引入框架柔顺。
4. 论文是振动扰动，现行模型是准静态路径。非同步脱离可支持事件/级联建模方向，但数值振幅、频率和动态稳定不能直接比对。

另有一项与本卡无关但必须保留：accepted C 的逐单元独立 \(u_{z_i}\) 与 proposed FORMAL 的刚性 C-R 边界之间已有 P0-SYS2；verification 要求明确二选一，见 `theory/review/DERIVATION_VERIFICATION_2026-07-17.md:409-420`。本文没有执行器端点/传力测量，不能替项目关闭该 P0。

## 4. 被漏掉的关键结论与建议补充

1. **P1 — A1 测量尺度门（schema + 验证义务）：** 增加 `native_spacing`、`registration_error`、`interpolation_spacing`、`trusted_min_wavelength`、`tip_radius_to_resolution` 和搜索方向坐标变换；插值不得改善可信带，失败返回 `GEOMETRY_UNCERTAIN`。
2. **P1 — 点级闭环验证（验证义务）：** 在留出墙面区域记录“几何候选→真实首次接触→摩擦可行→稳定承载”逐级命中/假阳性/假阴性。论文自己没有预测—实测点级准确率，见 `extraction_audit.json:184-187`；这正对应 accepted A 尚未关闭的 engagement criterion，`theory/modules/A_INTEGRATED_MODEL.md:1877`。
3. **P2 — 空球参考 oracle（可选验证模型）：** 只在离散点云和刚性半球适用域内实现 E2/E3，作为解析/网格后端回归，不把候选计数输出为概率或容量。
4. **P2 — 整爪功能输出（诊断字段）：** 输出纵/横对置组对力和力矩的贡献、驱动开关、局部脱离顺序和重平衡结果；功能角色随加载方向计算，不预设“主/辅”。
5. **P1 — 驱动撤除边界事件（条件模型/实验义务）：** 从同一 accepted 预紧态切换到经机构认证的 drive-off 边界，在同一位置重求；只有未来加入质量、阻尼、基座激励和重复实验后，才建立动态抗振扩展。

本卡不产生新的 P0。最优先是防止亚分辨率表面和驱动开/关边界被误实现；现有 P0-SYS2 继续由机构/CAD/合同审查关闭。

## 5. 明确不可直接移植

- 不移植扫描区尺寸、13,386 点、59/19 µm 误差、4 µm 插值、\(r=10/20\) µm、\(\theta_{min}=40/50^\circ\) 或 104/46/73 等候选计数；这些是特定砂石点云和算法配置，见 `evidence_card.md:148-154`。
- 不移植原型 431 g、17.5 mm 行程、12.7 N 驱动力，也不把驱动力当逐钩法向力；论文没有驱动力—接触力传递，见 `evidence_card.md:155`。
- 不移植 \(R_a\approx93\) µm、\(R_q\approx130\) µm 为通用粗糙度阈值；它们只描述一块磨石墙，见 `evidence_card.md:156`、`extraction_audit.json:189-192`。
- 不移植 12.3/12.5 Hz、开/关振幅、12 Hz/80%/1.6667 mm 工况或具体副爪脱离次序为本项目动力学参数/规律；无重复、误差带和接触力，见 `evidence_card.md:157-159`、`:170-182`。
- 不直接采用二维 E1、空球 E2 或 \(\theta_{min}\) 为生产级完整抓附判据；它们分别缺离面载荷/材料失效、噪声/邻域稳健性和摩擦映射。可保留为受限解析/趋势回归。

**总优先级：** P0 无新增；P1 关闭测量尺度门、点级验证和 drive-off 边界语义；P2 增加空球 oracle、半径/角度趋势回归及纵横对爪贡献诊断；P3 仅保存具体标记脱离顺序为单次试验观察。整体判断置信度高，M5/M6 的跨原型推广仅中等置信度。
