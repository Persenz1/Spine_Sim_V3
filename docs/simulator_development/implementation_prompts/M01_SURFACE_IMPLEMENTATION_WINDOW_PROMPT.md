# M01 SURFACE 实现窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。该窗口只实现冻结的 M01，不讨论或启动 M02、M03 或 M06。

## 提示词正文

~~~text
TASK_ID: M01_SURFACE_IMPLEMENTATION
PROMPT_VERSION: 1.0.0
REQUIREMENTS_VERSION: M01_SURFACE_REQUIREMENTS 1.0.0 frozen

本窗口只实现、测试和验收 M01 SURFACE：解析/合成 SurfaceRealization、确定性查询、按需多分辨率物化、M00 输出扩展和最小 2D/3D 预览。不得重新讨论冻结产品范围；不得实现 M02 数值延拓、M03 单刺接触、M04 阵列、M05 调度或 M06 正式绘图系统。

开始前必须完整读取：
1. README.md、theory/README.md；
2. docs/simulator_development/README.md；
3. docs/simulator_development/SIMULATOR_MODULE_PLAN.md；
4. docs/simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md；
5. docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md；
6. docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md；
7. docs/simulator_development/implementation/M00_FOUNDATION_TRACEABILITY.md；
8. theory/evidence_reassessment/README.md；
9. theory/evidence_reassessment/engineering_fixed_context.md；
10. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
11. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
12. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
13. theory/modules/A_INTEGRATED_MODEL.md；
14. theory/paper/MECHANISM_DERIVATION_FORMAL.md 中表面、有限球尖、最近特征与验证相关内容。

权威顺序：正式工程事实 > accepted system/A > M01 frozen 软件服务合同。FORMAL 0.2.0-proposed 只允许形成冻结需求已经批准的 additive provenance/schema/validation；不得借实现便利修改 accepted A 的 SurfaceRealization、完整球、接触、摩擦或状态语义。

实现前：
- 读取 git status --short，保留所有既有工作区改动；
- 复核 M00 当前 API、typed dataclass/enum、registry/writer/reader、strict config、unit/frame/status/hash 和测试风格；
- 使用现有 Python 3.12 src layout，新代码放在 src/spine_sim/surface，测试放在 tests/surface；
- 先形成简短计划和 M01 requirement-to-test traceability matrix；
- 纯软件内部选择自行完成，不向用户索要真实 PSD、Ra、摩擦或材料强度；
- 不读取或修改 archive，不修改 theory accepted 文件；
- 需要绘图依赖时将其隔离为 optional preview extra，surface evaluator import 不能要求绘图库存在。
- M00 现有 `test_project_has_no_plotting_runtime_dependency` 是 M00 阶段的临时全项目断言；若加入 optional preview extra，需把该测试收窄为“foundation/base runtime/evaluator 不依赖绘图”，保留 M00 架构语义而不是继续禁止未来模块出现任何绘图库字符串，并在追踪矩阵说明这一测试演化。

必须实现：

A. strict schema、身份和能力门
- SurfaceSourceDescriptor、SurfaceSpec、LatentNoiseIdentity、SurfaceRealization、SurfaceQueryHandle、CapabilityManifest 和 QueryResponse typed contracts；
- analytic/synthetic/measured 共同 schema、frame/unit/domain/material direction/provenance/status；
- analytic/synthetic SUPPORTED；measured parse/validate-only，create/query 返回 M01_MEASURED_IMPORT_DEFERRED 且不创建 realization ID/handle；
- production point-cloud/arbitrary-mesh import 同样安全 unavailable；
- M00 的 surface_spec_id/seed_id/surface_realization_id/hash/lineage、四栏 maturity、多轴 status 和 certification 标签；
- synthetic material_label 强制 synthetic_unidentified，拒绝真实材料冒名。

B. analytic surface library
- plane、slope_plane；
- directed 1D/2D sinusoid；
- Gaussian bump/pit 和 multi-Gaussian features；
- smooth/cosine、U/circular、V/piecewise-linear groove variants；
- known nearest-feature switch；
- VALIDATION_ONLY spherical cap/bowl；
- 每族声明参数域、光滑/不可微集合、boundary compatibility、exact/approximate/unavailable matrix；
- 实现 height/point/gradient/normal/available curvature 和 field-level status。

C. self-affine Gaussian generator
- 实现冻结 H、Sq/reference-Rt、lc/reference-Rt、anisotropy、direction 和 three-tier profiles；
- 150 x 150 mm periodic parent definition、冻结的 q_eff/anisotropy convention、zero mode、Hermitian/real construction、float64 和 ensemble-target normalization；
- 保存 target/realized PSD/directional spectrum/variance/real-valued error 及统计 scope；
- 使用 M01_PHILOX4X64_10_KEYED_1：SHA-256 从 root seed/namespace/seed index/latent namespace/band/role 派生 128-bit key，Philox counter 无碰撞编码 global lattice/mode signed coordinates 和 block ordinal；冻结 zigzag/width/endianness；版本化 Box–Muller normal transform/pair ordering；
- 绘图、线程、tile 和查询顺序不得推进 RNG；
- common-random-number latent identity 与 H/Sq/lc filter 分离；
- refinement 只能加入确定性高频模态，不能重随机低频或按 crop 归一化；
- 实现 hierarchical multiband spectral construction：全域粗低频层 + 坐标锚定的局部高频 lattice，活动 tile 通过带 halo 的 overlap-save/overlap-add FFT convolution 或满足全部冻结验收的等价 random-access spectral 算法生成；
- 禁止执行 150 mm parent 的最细全域 FFT；每 band 保存 filter/kernel/interpolation/derivative/FFT normalization、Hermitian/real rule、truncation/error bound；
- 证明 band 的线性 Gaussian 合成、target/realized PSD、Gaussian marginal、LOD nesting、crop/order invariance、tile seam 和资源上限；
- generator/version/profile 改变必须改变 realization identity，保留 golden replay fixtures。

D. logical domain、active footprint、tile 和 cache
- 区分 150 x 150 mm logical parent、derived active query footprint 和 materialized tile；
- 支持由 swept geometry envelope + guard 派生窄单刺/宽阵列活动走廊；100 mm 路径前后均有 guard；
- footprint 超域安全拒绝，不 wrap/clamp/缩短；
- 默认 256 x 256 core tile、明确 halo、content-addressed cache key 和 hash；
- 邻 tile 无缝、同坐标同值、窄/宽窗口重叠 bitwise 相同；
- 远区不生成或只给有 omitted-band bound 的 coarse representation；
- active tip region 按 Rt/5 -> Rt/8 -> Rt/10 refine；不能证明无接触时先 refine；
- memory cache payload 默认上限 512 MiB，disk cache 默认关闭且永远非 canonical；
- cache corruption 丢弃并重建，不能解释为物理不可行；
- 正常路径禁止构造全域 Rt/10 dense array。

E. SurfaceQuery
- 实现冻结需求第 9 节全部 scalar/typed-batch 语义；
- 每个 response 带 realization/query identity、capability、method/version、domain/quality/trust、status、requested/achieved tolerance、residual/error/convergence、unit/frame/reference；
- height differential、neighborhood/bounds、signed distance、all co-minimal closest features；
- exact primitive 与 approximate search 的 capability matrix；approximate 必须有全局候选覆盖、残量、error bound 和 convergence，失败时 unavailable/uncertain；
- non-smooth 处保留 one-sided feature/normal set，curvature field-level unavailable，不平均法向；
- query boundary 默认 ERROR；显式 compatible PERIODIC 返回 WRAPPED 和映射坐标；
- missing/quality mask 不能当作零高度或 NaN missing。

F. complete-sphere pure geometry
- 对 height field 实现 H_R(xc,yc) 和全部共最大支持；
- 对 generic path 实现 phi(c)-R 及 closest feature set；
- 验证两条路径零集/可行域一致；
- query R 只控制 probe/LOD，不进入 surface identity；
- API 和输出不得出现 needle axis/cap legality、摩擦、力、loaded contact、engagement、material failure 或 success；这些属于 M03/A。

G. validation-only mesh regression
- 实现 heightfield_triangulation_regression_adapter；
- 三角片最近点/距离能力只用于解析收敛 fixture；
- 外部 mesh/point cloud 仍 unavailable；
- adapter 不成为默认 provider，不让 preview grid 成为 solver geometry。

H. M00 result extension
- 注册 owner M01、namespace m01 的 ResultExtensionDescriptor；
- 实现 m01.surface_realizations、surface_provenance_steps、surface_quality_bands、surface_statistics、surface_materialization_receipts、surface_validation_results、source_availability；
- 实现选定 realization/window 的 visualization_height、visualization_validity、visualization_coordinates arrays；
- 字段元数据完整声明 semantics/class/dtype/shape/unit/frame/reference/index/status/source identity/maturity；
- 默认只保存 compact manifest，不保存 full fine domain；visualization arrays 仅显式选择并内容寻址去重；
- ResultReader round trip、default filtering、relations 和 schema freeze；
- 不保存每一个 transient query；M03 以后拥有 accepted contact/support raw output。

I. two-recipe minimal preview
- 独立 preview package/entry point，只实现 oblique_3d_surface 和 height_map_2d；
- 输入只来自 public visualization sampler 或已保存 M01 fields；不得读 evaluator 私有对象；
- 输出 PNG（可另加矢量格式）和 plot manifest；记录 realization/window/grid/unit/vertical exaggeration/colormap/recipe/version/source hash；
- 提供 150 x 150 mm、默认 1024 x 1024 的全域低分辨率 demo，以及可选 active/local preview；
- 全域粗 preview 使用显式 low-pass/area-average 和 visualization band，避免把 full fine band 点采样到粗网格产生 aliasing；
- gentle/medium/sharp 三档各生成 3D 与 2D 图，标题和文件名禁止真实材料名称；
- 不实现 engagement-angle heatmap、接触/力/材料图；审美与更多 recipe 留给 M06；
- plotting optional dependency 不存在时，provider/query/writer/reader 必须正常导入和运行。

J. validation reports
- analytic/finite-difference、SDF/closest、sphere-envelope、PSD/variance/real error、seed replay、tile/LOD/footprint、boundary/mask、mesh regression、M00 schema/reader 和 preview 测试；
- 产生代表性 profile、slope/normal、distribution、PSD/directional spectrum、trust band 和 resolution convergence 的 VALIDATION_ONLY 证据；这些不是新增 user-facing preview recipes；
- Rt/8 与 Rt/10 默认几何门：envelope/clearance <= 0.01 Rt、unique support position <= 0.02 Rt、normal angle <= 1 deg、非切换区 topology 不变；
- Hermitian/imaginary relative residual <= 1e-12；coefficient variance/Parseval 在 generator contract 的 float64 容差内；
- sampled PSD 按统计包络/ensemble 验证，不要求随机单 realization 逐 bin 精确命中 target；
- serial/parallel、plot-before-query、tile order、cache hit/miss、narrow/wide footprint invariance；
- measured/mesh safe unavailable 和 cache corruption regeneration；
- 测试失败必须分数值失败、capability unavailable、domain/quality invalid，不能只返回 false。

K. README、demo、performance 和 traceability
- 在 M01 模块 README.md 写简短“## 输出概览”，说明消费者、dataset/array、索引、unit/frame、status、ResultReader 最小读取、source/maturity/certification；
- 自动测试 README 引用的 schema ID 确实存在；
- 生成冻结需求第 14.6 节完整 VALIDATION_ONLY demo；
- 生成 M00 canonical bundle 并经 ResultReader 读回；
- 生成需求—实现—测试追踪矩阵、validation report 和 performance report；
- 性能报告记录硬件/OS/runtime/dependency/thread/fixture/footprint/LOD、peak RSS、cache payload、tile counts、generate/query/plot time 和 artifact sizes；
- 明确证明正常路径未创建 full-domain Rt/10 dense grid，memory cache payload 不超过 512 MiB；
- 报告当前 experimentally_validated 仍为 NOT_ASSESSED/BLOCKED_UNAVAILABLE，全部 synthetic 仍 not_certifiable。

明确禁止：
- 实现或假装支持白光轮廓仪、实测点云/mesh 生产导入；
- 生成名为真实红砖/混凝土的表面；
- 用单一 Ra 唯一决定 3D 表面；
- seed-only replay、crop normalization、tile-local RNG、query-order RNG 或 refinement rerandomization；
- 把 visualization grid 作为唯一求解几何；
- 无保守 bound 时用 coarse LOD 排除接触；
- M01 返回 contact force、legal cap、engaged/success、material failure、actual engagement angle 或 ranking；
- M01 导入 A/M02/M03/M04/M05/M06 的内部 package；
- preview package 被 surface evaluator 反向导入；
- 修改 M00 core schema、accepted theory 或 archive；
- 自动开始 M02、M03 或 M06。

完成前：
1. 运行全部 M00 回归和新增 M01 tests；
2. 运行 lint、type、schema、link、import-boundary、replay、performance 和 demo checks；
3. 重新读取 git status --short，保留无关工作区改动；
4. 校验 requirement-to-test traceability 和 M00/A/DEV profile consistency；
5. 只精确暂存 M01 实现、测试、demo、README、reports 和本窗口明确批准的关联文件；
6. 禁止 git add -A、git add .；
7. 使用 git diff --cached --name-only 与 git diff --cached --check；
8. 不提交、不格式化、不回退任何无关改动；
9. 提交并推送前核对当前分支和 origin 是用户已授权的可信目标；
10. 报告 commit、实际文件、测试/性能、demo bundle、2D/3D 图片路径、资源用量和 unavailable 能力；
11. 停止，不得开始 M02、M03 或 M06。
~~~
