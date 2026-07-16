# C_INTEGRATION-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-17`  
> 网页原件/候选副本 SHA-256：`65fc8b40e9dfde0bcf47842bd37535b5f3a56cad6dd31d49510208642e832043`  
> 正式 C 模型 SHA-256：`8439835281ed61344de106082f8e6826c9a993d8767fb7845633510cdfe5b589`

## 产物、归档与运行身份

- 网页下载原件按原文件名和原始字节保存到 `derivation/runs/C_INTEGRATION/raw_downloads/`；规范化候选与下载原件逐字节一致。`RAW_RESPONSE.md` 保存本轮仅附件交付的响应标记。
- 运行身份为 `C_INTEGRATION-r01`，实际目录为 `derivation/runs/C_INTEGRATION`，没有覆盖历史。网页输入仍由冻结 Git 提交、逐文件字节数和 SHA-256 可复现。
- 正式接受版写入 `derivation/modules/C/final/C_INTEGRATED_MODEL.md`。该版本文件本身是 `1.0.0 accepted` 快照；运行目录另已冻结原件和候选副本，因此无需再复制第三份相同历史快照。
- 候选到接受版差异仅为文件身份转正和一处无歧义的异常状态并列分支符号修正；方程、物理分支、范围、数值和工程事实未改变。

## C1、C2、C3 继承与一致性集成

- C1 的唯一共同搜索坐标、四单元 `UX_PZ_BALANCED` 调用、法向 graph、共轭搜索反力、对置预紧、联合停止门控、安全/行程/碰撞/认证、事件与 DamageStore 协调、原子提交及 `s_stop` 锁定均已保留。
- C2 的刚体姿态、四单元完整 twist、参考点/wrench 运输、50 mm 偏心加载点、六维平衡、固定姿态无隐藏支承、X/Y 小角度 rocking、yaw 禁用、一侧稳定性和 B 运动覆盖审计均已统一。
- C3 的针级事件、单元显著退化、事件后四单元完整重调、可恢复/不可恢复脱附、原始稳定反力曲线、光滑/尖点/平台/多峰、峰后继续、分支可达性和 `F_crit` 确认条件均已保留。
- 三个历史 accepted state 已映射为唯一 `CAcceptedState`；阶段、互斥主状态、正交事件/里程碑、诊断、低层 opaque 句柄和事务身份分开，没有三套竞争的当前状态。

## 坐标、符号、单位、功和去重

- 四个右手局部坐标、`O_i`、`O_A`、非零偏置、80 mm×80 mm 空区力臂、C 点和加载点只有一个规范定义。旋转矩阵、加载力矩、rocking 法向位移和 wrench–twist 功不变性已通过解析回归。
- mm、N、N·mm、rad、s、N/mm 和无量纲通道已分开；N 与 N·mm 不能未经版本化尺度构造欧氏范数。
- B 返回的 `A_on_B` contact-only wrench 只运输和装配一次；`P_i`、共同径向驱动、加载器、真实授权约束和未授权乘子已分栏。
- C1 的理想 `-P_i du_zi` 与完整执行器功已拆成 `ideal_generalized_force_work`、`certified_relative_actuator_work` 和 `unavailable`；端点/作用线未认证时不以零填充。
- 球尖接触、针梁、针级轴向弹簧/硬限位、阵列兼容/载荷共享和材料损伤仍分别由 A/B/DamageStore 拥有。C 不添加接触、梁、弹簧或框架柔顺；rocking 是刚体自由度，`eta_i` 不是第二根针级弹簧。

## 状态、事件、单步算法与能力

- 物理事件的路径最早性与诊断主状态优先级已分开；所有原始状态码、同时事件组、事件前/点/后状态和里程碑都保留。
- 共享 DamageStore 由 B/A 协调器生成 fixed point；C 只组织跨单元冲突图、四单元重调、同位置级联、状态哈希/Zeno 防护和全局原子提交。
- 21 步统一算法完整覆盖身份冻结、阶段和路径、运动合同审计、四单元无副作用 trial、wrench/功检查、平衡、最早事件、损伤 fixed point、级联、稳定性、退化、曲线/峰值、`F_crit`、prepare、commit、rollback 和规范响应。
- 首针失效、单元显著退化、首峰、物理无平衡、物理失稳和可恢复/不可恢复脱附互不等价。只有认证、可达、稳定且已提交的分支可进入原始反力曲线和能力确认。

## B 1.0 覆盖缺口与公共接口

- `B_TO_C 1.0.0 accepted` 仅认证每单元局部 x 和全局 Z 平移；四单元允许平移子空间的交集只有全局 Z。正式 `+X` 对 ±Y 单元需要局部 y，`45°` 对四单元都需要局部 y，rocking 还需要动态姿态/表面/碰撞和 6D graph。
- 因此在 B 2.x 完整 twist/姿态扩展被正式接受前，非零正式偏心加载唯一合法结果为 `C_CONTRACT_EXTENSION_REQUIRED`；`delta_P`、B/A、DamageStore、事件、功、曲线和峰值均不推进。该状态不是零能力、物理无平衡、失稳、脱附或数值失败。
- 文件仅保留 B 2.x 的版本化扩展要求和关闭验证，没有把它写成已接受合同。
- 嵌入式公共接口完整覆盖 C→B 请求、B→C 保留响应、capsule 失效与完整回调条件、系统请求/响应、opaque 状态所有权、认证等级和实验原始输出。

## 未决项、验证边界与可复现检查

- C1 停止阈值/窗口/滞回与 `s_max`、B 2.x、执行器端点与 `eta_i`、rocking 有效域、材料/表面/损伤参数、事件/稳定/峰值/分支数值策略、C 加载速度、统计样本和实验误差均保持未决并具有安全处理与关闭条件。
- 正式 `accepted` 只表示 C 理论、数据对象和公共接口集成通过当前语义审查；不表示 B 2.x、求解器、CAD/机构绑定、材料参数或目标实验已验证。
- Markdown 代码围栏、显示/行内数学定界符和 0–21 节结构闭合；无模板占位符。候选→接受版转换由校验器逐字确认。
- 数学回归覆盖四个右手旋转矩阵、50 mm `+X/45°` 力矩、两种方向的四单元局部 x/y 分解、rocking 法向位移符号和非零参考点下的 wrench–twist 功不变。

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C_INTEGRATION/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C_INTEGRATION/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

三条命令均已通过。C 大模块集成到此结束；本轮未启动下一大模块或全局 A/B/C 集成。
