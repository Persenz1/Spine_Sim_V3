# C3-r01 验证报告

> 结论：`pass / accepted`
> 处理日期：`2026-07-17`
> 接受版 SHA-256：`810fc26972652086403181f97221503e08e267485c6bd31fe1ea44b5af9a8f66`

## 产物与归档

- 四个网页下载原件已按浏览器实际文件名原样保存到 `derivation/runs/C3/raw_downloads/`；逐文件字节数和 SHA-256 已写入 `INPUT_MANIFEST.yaml`，并与下载源复核一致。
- `RAW_RESPONSE.md` 保存随四个附件收到的网页文本回答；原始下载和原始回答均受 `.gitattributes -text` 保护。
- 规范候选保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml`、`RUN_UPDATE_SUMMARY.yaml` 和 `CITATION_BRIEF.md`。除接受版模块上下文的八项状态元数据规范化外，候选工作副本均与对应下载原件逐字节一致。
- `MECHANICAL_FIXES.md` 记录了全部机械处理；没有回写原件，也没有修改物理方程、工程事实或证据边界。

## 工程事实与运行摘要

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 基线均为 37148 字节，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`，完整 diff 为空。
- `RUN_UPDATE_SUMMARY.yaml` 可由 PyYAML 解析；`run_id=C3-r01`、模块、提示词版本、基线版本和 `run_directory=derivation/runs/C3` 正确。
- `engineering_context_delta` 唯一条目符合 `operation: none` 合同：目标和候选事实为空、修改字段和四类证据列表为空、无需审批。
- 工程事实生成器通过：9 个领域、48 条事实；正式工程事实、schema、manifest、provenance 与生成视图没有变化。

## 模块继承与语义边界

- 输出是融合 C1+C2+C3 的完整 C 模块上下文，共含编号主章节 0–48；C1/C2 的第一篇和第二篇与冻结的 `C_MODULE_CONTEXT 0.2.0 accepted` 主体逐字一致，C3 在文件头/权威说明之后追加第 31–48 节。
- C1 的 `s_stop`、四个 B/A accepted snapshots、共享 DamageStore、事件/级联、功/能量、哈希、确定性重放和原子事务均保留；C2 的刚体运动学、wrench 运输、偏心六维平衡、rocking、稳定性和无隐藏支承原则均保留。
- C3 建立了不可丢失原始 B/A 历史的单元 continuation capsule，并明确局部低维 response/graph 的 trust region 与强制完整 B 回调条件。
- 针级滑移、材料/强度、硬限位、释放、脱离和再挂接保持细分；`FIRST_NEEDLE_FAILURE`、`FIRST_UNIT_SIGNIFICANT_DEGRADATION`、整体峰值候选和最终能力相互分离。
- 任一事件后必须从同一 accepted state 和 DamageStore 基线重调四单元、协调共享损伤、重求允许姿态与六维平衡并处理同位置级联；均分、邻接权重、固定矩阵、旧峰值缩放和单元峰值求和均被禁止。
- `F_reaction(delta_P)` 只接收经认证、可达、稳定且已提交的曲线点；`F_crit` 定义为稳定可达分支上的上确界/最大值，候选峰和最终确认严格分离。首峰后若仍有合法稳定分支必须继续位移加载，以保留下降段、再平衡、再挂接和二次峰。
- 物理无平衡、物理失稳、可恢复/不可恢复脱附、合同/模型/参数/域/数值/事务停止分别报告；非物理停止不得冒充物理终点或 `F_crit`。
- 当前 `B_TO_C 1.0.0` 仍不认证正式 `+X/45°` 所需局部 y 和姿态运动；非零正式请求必须返回 `C3_CONTRACT_EXTENSION_REQUIRED` 并保持历史不前进。本次接受不表示 B 2.x 已实现或获批。
- 第 47 节只形成下一阶段交接；本轮没有生成 `C_INTEGRATED_MODEL.md`，也没有开始 C 集成或全局集成。

## 引用与证据检查

- `CITATION_BRIEF.md` 只引用本轮实际上传的文献 23、文献 28 和明确标界的 GPT 通用知识；正文引用集合与文末定义均为 `[1]–[3]`，没有未使用或未定义编号。
- 本轮未使用外部网络资料，文件中没有外部网址；无需网络来源复核。
- 文献 23 只支持活动集切换、剩余分支增载和等刚度特殊基准；文献 28 只支持固定活动集的整体平衡与最弱裕度骨架。论文常数、砂纸/足数/几何/速度和常数能力域均未迁移为项目工程参数。
- 引用说明中列出的工程事实 ID 全部存在于当前结构化事实库；引用说明明确为仅本轮本地归档，不进入下一任务上传链、模块上下文、集成模型或工程事实审批。

## 可复现力学与格式校验

- `+X` 加载得到 `M_Y=+50F N·mm`；`45°` 加载得到 `M_X=-50F/sqrt(2)`、`M_Y=+50F/sqrt(2)`；成对法向力差得到文档声明的 40 mm 半跨距力矩。
- 等刚度特殊极限满足失载守恒；非等刚度构造产生非均分结果，验证文献 23 公式只能作为特殊回归基准。
- 构造的 stable/reachable/certified/accepted 集合只纳入合法曲线点，未提交或未认证高反力点不会进入 `F_crit`。
- 故障注入下，`delta_P`、整体位姿、四单元状态、DamageStore、事件和峰值账本保持原子回滚。
- 当前版、候选版和引用说明均通过 Pandoc Markdown 解析；代码围栏、显示数学块、主章节、28 项 C1、30 项 C2、26 项 C3 验证矩阵、必需状态码、模板残留和规范文件 whitespace 检查通过。`RAW_RESPONSE.md` 中网页原文自带的行尾空格按字节保真要求保留，不作为机械修复对象。
- `current/C_MODULE_CONTEXT.md` 与 `history/C_MODULE_CONTEXT_after_C3.md` 均为 200666 字节且逐字节一致，状态为 `accepted`，版本为 `0.3.0`。

## 接受边界

本次接受的是 C3 理论上下文、事件/接口/数据合同、峰值与终止定义以及安全拒绝语义。它不表示 `B_TO_C 2.x` 已实现或获批，也不表示求解器代码、材料/表面参数、显著退化阈值、峰值/事件容差、数值收敛、分支探索、执行器作用线、真实试验架约束或目标实验已经完成。这些项目继续作为接受上下文中的显式未决项。

没有工程事实变化、实质语义冲突或需要人工取舍的物理机理，因此不触发人工决策。

## 可复现命令

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C3/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C3/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
pandoc --from=markdown --to=native derivation/modules/C/current/C_MODULE_CONTEXT.md
pandoc --from=markdown --to=native derivation/runs/C3/MODULE_CONTEXT_CANDIDATE.md
pandoc --from=markdown --to=native derivation/runs/C3/CITATION_BRIEF.md
```

上述检查均通过。
