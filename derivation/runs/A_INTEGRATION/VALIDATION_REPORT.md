# A_INTEGRATION-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-16`  
> 正式 A 模型 SHA-256：`0679f5bfe71d2ff5b2521414a39b41c6b94f23f54227d19bd38a964960088ccc`  
> 正式 A→B 合同 SHA-256：`02d557c799973aad2347a255767c6b9283d9225a3c1a8e87ead91f6debc253df`

## 产物与归档

- 两个网页下载原件均按原文件名原样保存到 `derivation/runs/A_INTEGRATION/raw_downloads/`；字节数和 SHA-256 与接收源一致。
- 两个规范化候选与下载原件逐字节一致，分别归档为 `A_INTEGRATED_MODEL_CANDIDATE.md` 和 `A_TO_B_CONTRACT_CANDIDATE.md`。
- `RAW_RESPONSE.md` 保存本轮随附件收到的完整文本消息；所有接受版修复记录于 `MECHANICAL_FIXES.md`，未回写原始回答或下载原件。
- 正式结果已写入 `derivation/modules/A/final/A_INTEGRATED_MODEL.md` 和 `derivation/contracts/A_TO_B_CONTRACT.md`。最终集成模型本身是 A 模块冻结快照，运行目录同时保留候选—接受版关系，未创建内容重复的额外快照。

## 输入、运行身份与工程事实

- 运行身份为 `A_INTEGRATION-r01`，实际目录为 `derivation/runs/A_INTEGRATION`；未覆盖任何历史运行。
- 冻结的三个网页输入仍由 `repository_commit`、逐文件字节数和 SHA-256 复现；A1、A2、A3 接受快照和验证报告全部一致，当前 `A_MODULE_CONTEXT` 与 after-A3 快照逐字一致。
- 工程事实仍为 `engineering_fixed_context 1.0.0`，生成器校验通过：9 个领域、48 条事实。本轮没有工程事实变化，也没有固定未决参数、扫描集合、坐标、边界、开关或首版范围。

## 三个子模块的继承与一致性集成

- A1 的 `SurfaceRealization/A1QueryHandle`、有限球尖/合法球冠、欧氏间隙、多支持、方向候选、全复合针体禁止碰撞、质量/域状态和安全增量接口均保留；A1 原始地形保持不可变。
- A2 的 Signorini–Coulomb SOC 互补、最大耗散、梁柔顺、无拉力轴向弹簧、4 mm 硬限位、刚性/柔性开关、残量分块和稳定性/退化诊断均保留。
- A3 的客观滑移、三维支持迁移、局部材料容量、不可逆损伤、针体强度、释放/可逆回位、继续搜索、再预载、再挂接、共享 `DamageStore` 和连续 100 mm 多峰记录均保留。
- 正式模型把 A 重构为 `intrinsic_single_spine_kernel` 与 `standalone_single_spine_driver` 两层：前者接受 B 规定的基座位姿/增量且不含每针 0.5 N 残量；后者只用于 A 层独立验证，在核外施加固定 0.5 N、搜索/同伦和 100 mm 路径。B 的每单元 0.5–2 N 主动推力因此只在 B 外层施加一次。

## 符号、单位、功、柔顺与失效审查

- 公共 wrench 唯一定义为 A 对 B、在声明参考点和坐标表达的力/矩；作用—反作用、参考点运输、坐标变换和基座增量功共轭闭合。力矩统一使用 N·mm，弹簧 N/m 在入核前除以 1000 转为 N/mm。
- 未变形结构/弹簧轴 `\mathbf a_0` 与当前球冠轴 `\mathbf a_t` 已区分；梁截面合矩、材料力矩利用率、针体主拉应力上界、接触点柔顺映射和稳定零空间均已在文件内定义。
- 局部接触柔顺、露出针梁、轴向弹簧、刚性背板/硬限位和未来根部柔顺具有独立状态、共轭力、位移和能量；没有用同一总斜率重复标定。
- A2 材料检查钩子不再与 A3 材料容量重复；墙面材料失效、针体上限、梁模型越界、体部碰撞、接触释放、物理无解和数值不收敛分别拥有唯一判据和错误分类。
- 离散功平衡分别记录梁/弹簧/接触储能、Coulomb 与材料耗散、释放可恢复能和数值误差；trial/rollback 不累计任何物理历史。

## 状态、事件、算法、未决问题与合同

- 互斥主机械状态以及接触、弹簧、材料、针体、质量/求解正交子状态闭合；瞬时事件不再伪装为驻留状态。
- 固定致命优先级仅为输入域/质量不足优先 1、锥段/针杆/安装座碰撞优先 2；其他接触、摩擦、支持、弹簧、材料、针体和退化事件在共同最早位置竞争，并执行一侧一致性检查。
- 单步算法完整覆盖 snapshot、分支预测、全粘着、支持/滑移/损伤活动集、半光滑求解、事件括区、完整重求解、功/质量检查、原子 commit/rollback、剩余增量循环和零长度事件保护。
- `UNRESOLVED.REGISTRY.GLOBAL` 及其 20 个具体工程未决 ID 全部保留；实现、CAD、材料/针体标定、容差、随机样本和实验关闭条件没有因规范接受而被误标为完成。
- 独立 `A_TO_B_CONTRACT.md` 可单独阅读；标记范围内的合同正文与集成模型第 12 节逐字一致。合同冻结唯一调用模式、输入/输出、wrench 方向/单位、事件分数、切线状态、错误分类、共享损伤协调、原子事务和 B 的禁止事项。

## 无歧义修复和可复现检查

- 网页候选完整覆盖正式提示词要求；接受版只进行了身份转正、符号统一和从已接受 A3 唯一补回的缺失定义，没有改变工程事实、物理分支或范围。
- Markdown 代码围栏、显示/行内数学定界符和合同标记闭合；正式文件无模板占位符，独立/嵌入合同正文逐字一致。
- 数学回归覆盖：wrench 参考点运输的功不变性、SOC 滑移最大耗散、梁柔顺矩阵对称性、弹簧单位换算、有限控制体牵引一致性、Mohr–Coulomb 边界、软化端点与完整断裂能、圆截面/主拉应力上界；全部通过。

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/A_INTEGRATION/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/A_INTEGRATION/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

三条命令均通过。A 集成到此完成；求解器实现、合同实现测试、材料/针体标定、几何/CAD、数值收敛和实验验证仍按正式模型中的关闭条件继续保持未决。
