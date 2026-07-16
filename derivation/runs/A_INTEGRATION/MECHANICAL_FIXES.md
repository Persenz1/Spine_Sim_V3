# A_INTEGRATION-r01 机械与无歧义完整性修复记录

两个网页下载原件按原文件名和原始字节完整保存在 `derivation/runs/A_INTEGRATION/raw_downloads/`。`A_INTEGRATED_MODEL_CANDIDATE.md` 和 `A_TO_B_CONTRACT_CANDIDATE.md` 与对应下载原件逐字节一致；以下修复只作用于正式接受版。

1. 将正式模型和合同从网页交付身份 `1.0.0-candidate / candidate` 规范为本地审查后的 `1.0.0 / accepted`，并同步独立合同文件头、嵌入合同身份表和调用版本。接受状态只表示推导规范冻结，不表示求解器、参数或实验已经验证。
2. 统一未变形结构轴为 `\mathbf a_0`、当前针尖球冠轴为 `\mathbf a_t`：梁柔顺、轴向弹簧广义力和弹簧点柔顺使用 `\mathbf a_0`，球冠合法性查询使用 `\mathbf a_t`；同时把梁式中的针尖截面合矩统一为已定义的 `\mathbf M_c^{c_t}`。这只消除候选中的下标漂移，不改变 A2 已接受拓扑或力方向。
3. 候选首次失效式引用了未在集成文件中展开的 `\Phi_{M,k}`、Mohr–Coulomb、拉伸截断和可选压帽。接受版从 `A_MODULE_CONTEXT 0.3.0 accepted` 唯一补回 `\mathbf q_{M,k}`、`r_{M,k}`、`\Phi_{M,k}`、材料方向变换和各容量面，并明确无力矩/压帽标定时关闭相应分支；未新增材料参数、容量函数或默认数值。
4. 补回候选已使用但未定义的截面半径 `R=d/2`、最大主拉应力上界 `\sigma_1^{\rm ub}`、接触点位移映射 `\mathbf J_r`、结构稳定切线 `\mathbf K_{\rm str}` 及零空间基 `\mathbf N`。这些定义均来自已接受 A2/A3 方程或其唯一符号映射。
5. 明确面片汇聚力的压缩/切向分解、压帽偏应力和混合模态软化量的单位/冻结时机，使材料容量、软化和耗散链在正式集成文件内自包含。
6. 在未决问题章节显式标注其逐项展开 `UNRESOLVED.REGISTRY.GLOBAL`，并把“本候选中的状态”规范为“本模型中的状态”；所有 20 个具体工程未决 ID 及关闭条件保持不变。
7. 所有合同身份和兼容性文字在独立合同与集成模型嵌入正文中同步修改；两个 `BEGIN/END A_TO_B_PUBLIC_CONTRACT` 标记之间的内容仍逐字一致。

本轮没有修改 `engineering_fixed_context 1.0.0`，没有新增或选择工程数值、材料分支、物理范围或 B/C 层机理，也没有需要人工决定的语义冲突。
