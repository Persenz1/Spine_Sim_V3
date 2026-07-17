# B1-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-16`  
> 接受版 SHA-256：`a4b9ae655fdabb82b72dffadfa3b6f0024cbba225120b51c26e96c201261616a`

## 产物与归档

- 四个网页下载原件均按下载文件名原样保存到 `derivation/runs/B1/raw_downloads/`，逐文件字节数和 SHA-256 已写入 `INPUT_MANIFEST.yaml`。
- 规范化候选保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md`；四份候选均与对应原件逐字节一致。
- `RAW_RESPONSE.md` 保存本轮随附件收到的完整网页文本回答。
- 接受版已更新为 `derivation/modules/B/current/B_MODULE_CONTEXT.md`，并保存等字节历史快照 `derivation/modules/B/history/B_MODULE_CONTEXT_after_B1.md`。
- `CITATION_BRIEF.md` 只在 B1 运行目录归档，不进入 B2 默认上传链。

## 输入与运行身份

- 运行身份为 `B1-r01`，实际目录为 `derivation/runs/B1`；提示词、输入清单和 10 个上传路径的数量、顺序、字节数与 SHA-256 一致。
- 冻结提交 `7274c26dd7d8db72f565046d8cb8032b172b8db0` 中的全部网页输入与 `INPUT_MANIFEST.yaml` 一致；正式提示词与运行归档副本逐字节一致。
- A 模块集成结果和 `A_TO_B_CONTRACT 1.0.0 accepted` 复验通过；文献 04、07 压缩包均包含 `evidence_card.md` 和三幅关键图，CRC 通过。

## 工程事实与运行摘要

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 逐字节一致，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`。
- `RUN_UPDATE_SUMMARY.yaml` 可解析；运行身份、`operation: none`、空证据列表、`proposed_fact: null` 和审批标志符合无变化合同。
- 工程事实生成器通过：9 个领域、48 条事实。没有固定数值、扫描集合、坐标、边界、模型开关、首版范围或未决登记变化，无需人工审批工程事实。

## 模块完整性、语义和边界

- 候选是 B 截至 B1 的首版完整上下文，覆盖阵列索引与身份、固定角/梯度几何闭合、共同刚性背板运动、刚性/独立弹簧拓扑、实际针长绑定、方向性与空间相关性、针级广播、A 请求骨架、验证及 B2/B3/C 交接。
- `r=0` 根部排、`c` 随局部 `+y`、规则球心投影格点、梯度 `L_r sin(alpha_r)=4 sin(80°)`、安装座反算和共同 x/z 平移相互一致；`2×5` 与 `5×2` 保持有向分离向量和包络差异。
- B 只使用 `embedded_constitutive_trial`，保留 `A_on_B` wrench、A 状态所有权、共享损伤快照、事件/质量/非唯一性和事务字段；没有把每单元主动推力改写成每针法向载荷。
- B1 未提前求解接触力、弹簧平衡、活动接触集、载荷共享、失效重分配、级联、再挂接或整爪平衡；这些边界分别留给 B2、B3 和 C。
- 真实 CAD 可装配、制造误差、表面相关性参数、高碳钢参数、弹簧/主动推力离散点和数值容差继续显式保持未决，没有隐藏默认值。
- 未发现需要人工取舍的工程事实或物理机理冲突；接受仅表示 B1 规范和接口完成审查，不伪装为代码、CAD、测量或实验验证完成。

## 无歧义修复与可复现验证

- 接受版文件头和第 15.4 节的归档状态统一为 `accepted`；上下文版本保持 `0.1.0`，物理公式、参数和边界未改动。
- 公式级检查覆盖 `n_x,n_y∈{2,…,6}` 与 `s∈{4,5,6} mm` 的全部 75 个组合；针数、唯一性、质心和包络全部闭合。
- 两种梯度在全部 `n_x=2…6` 上通过角度插值、长度补偿、安装座共面和球心正反闭合检查；`2×5`/`5×2` 的二阶有向偏移计数通过。
- wrench 参考点运输在当前零转动共同平移子空间保持虚功不变；Markdown 代码围栏、数学块、章节和方程标签闭合。
- 当前 B 上下文和 `CITATION_BRIEF.md` 均通过 Pandoc Markdown 解析；当前上下文与 B1 历史快照逐字节一致。

## 引用核验

- `CITATION_BRIEF.md` 的 6 项顺序引用均在正文使用且有定义；本地文献只写“文献04/07”，GPT 通用知识明确说明内容和适用边界。
- RFC Editor 的 RFC 8785 页面、NIST 的 FIPS 180-4 页面和 NIST/SEMATECH autocorrelation 页面均可访问，分别支持确定性 JSON 规范化、SHA-256 标准和相关性概念的实现说明。
- 文献 04/07 的角度、行程、回差和载荷数据均保留迁移边界，没有升级为本项目固定参数。

## 可复现命令

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B1/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B1/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

三条命令均通过。需要真实 CAD、材料/表面参数、求解器实现或实验输入的检查继续作为 B1 接受上下文中的显式未决验证。
