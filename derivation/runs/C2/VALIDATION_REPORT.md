# C2-r01 验证报告

> 结论：`pass / accepted`
> 处理日期：`2026-07-17`
> 接受版 SHA-256：`7aa3c9a6a2e6f16886e7ec14674f0503d1d3794f8c70fab2942ab3d178ec6f65`

## 产物与归档

- 四个网页下载原件已按浏览器实际文件名原样保存到 `derivation/runs/C2/raw_downloads/`；逐文件字节数和 SHA-256 已写入 `INPUT_MANIFEST.yaml`，并与下载源复核一致。
- `RAW_RESPONSE.md` 保存随四个附件收到的网页文本回答；原始下载和原始回答均受 `.gitattributes -text` 保护。
- 规范候选保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml`、`RUN_UPDATE_SUMMARY.yaml` 和 `CITATION_BRIEF.md`。除接受版模块上下文的四项状态元数据规范化外，候选工作副本均与对应下载原件逐字节一致。
- `MECHANICAL_FIXES.md` 记录了全部机械处理；没有回写原件，也没有修改物理方程、工程事实或证据边界。

## 工程事实与运行摘要

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 基线均为 37148 字节，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`，完整 diff 为空。
- `RUN_UPDATE_SUMMARY.yaml` 可由 PyYAML 解析；`run_id=C2-r01`、模块、提示词版本、基线版本和 `run_directory=derivation/runs/C2` 正确。
- `engineering_context_delta` 唯一条目严格符合 `operation: none` 合同：目标和候选事实为空、修改字段和四类证据列表为空、无需审批。
- 工程事实生成器通过：9 个领域、48 条事实；正式工程事实、schema、manifest、provenance 与生成视图没有变化。

## 模块继承与语义边界

- 输出是融合 C1+C2 的完整 C 模块上下文，共含编号主章节 0–30；C1 的第 1–14 节与 `C_MODULE_CONTEXT_after_C1.md` 逐行一致，第 15 节只更新为历史自检和 C2 滚动上下文说明。
- C1 的 `s_stop`、四个 B/A accepted snapshots、共享 DamageStore、事件/级联、功/能量、哈希、确定性重放和原子事务均保留；C2 没有重置或重建上游历史。
- C2 明确定义 C、P 与四个 `O_A` 的 twist Jacobian、wrench 对偶运输、`+X/45°` 的 50 mm 偏心外载、80 mm 对置力臂、六维 contact-only 装配、固定/rocking 模式和无隐藏支承条件。
- `P_i` 的 B 输入、执行器功、系统边界和 contact-only wrench 已分栏，没有重复加入墙面承载。
- 当前 `B_TO_C 1.0.0` 对局部 y 平移与真实姿态更新的缺口被证明并映射为 `C2_CONTRACT_EXTENSION_REQUIRED`；最小 `B_TO_C 2.0.0` 要求、向后兼容、最后有效状态和安全拒绝路径齐全。没有旋转旧 wrench、x/z 投影或冻结针姿态来伪造支持。
- C3 只接收完整 `C2AcceptedState` 和未决扩展条件；本轮没有提前定义渐进失效后的整体峰值或峰后终止。

## 引用与证据检查

- `CITATION_BRIEF.md` 只引用本轮实际上传的文献 17、文献 28 和明确标界的 GPT 通用知识；正文引用集合与文末定义均为 `[1]–[3]`，没有未使用或未定义编号。
- 本轮未使用外部网络资料，文件中没有外部网址；因此无需进行网络来源复核。
- 文献 17 只支持压力中心/分支 wrench/六维装配骨架，文献 28 只支持整体平衡、最弱裕度和姿态适应低阶结构；论文常数、峰值、被动腕参数和整机实验结果均未迁移为项目工程常数。
- 引用说明明确为仅本轮本地归档，不进入下一任务上传链、模块上下文、集成模型或工程事实审批。

## 可复现力学与格式校验

- 随机 wrench/twist 的四单元参考点运输满足虚功不变；`rho=0` 时 rocking 四个法向位移符号为 `(+40 theta_Y, -40 theta_Y, -40 theta_X, +40 theta_X)`。
- `+X` 加载得到 `M_Y=+50F N·mm`；`45°` 加载得到 `M_X=-50F/sqrt(2)`、`M_Y=+50F/sqrt(2)`；成对法向力差得到文档声明的 40 mm 半跨距力矩。
- 全局 `+X` 平移对 `±Y` 单元产生局部 y；`45°` 平移对四单元均产生非零局部 y，合同覆盖审计的几何结论通过构造检查。
- 失败注入下，`delta_P`、整体位姿、四单元状态、DamageStore 和事件均保持原子回滚。
- 当前版、候选版和引用说明均通过 Pandoc Markdown 解析；代码围栏、显示数学块、主章节、30 项 C2 验证矩阵、必需状态码和模板残留检查通过。
- `current/C_MODULE_CONTEXT.md` 与 `history/C_MODULE_CONTEXT_after_C2.md` 均为 120064 字节且逐字节一致，状态为 `accepted`，版本为 `0.2.0`。

## 接受边界

本次接受的是 C2 理论上下文、接口要求和安全拒绝语义。它不表示 `B_TO_C 2.x` 已实现或获批，也不表示求解器代码、材料/表面参数、数值收敛、摇摆有效角域、执行器作用线、真实试验架约束或目标实验已经完成。以上项目继续作为接受上下文中的显式未决项。

没有工程事实变化、实质语义冲突或需要人工取舍的物理机理，因此不触发人工决策。

## 可复现命令

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C2/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C2/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
pandoc --from=markdown --to=native derivation/modules/C/current/C_MODULE_CONTEXT.md
pandoc --from=markdown --to=native derivation/runs/C2/MODULE_CONTEXT_CANDIDATE.md
pandoc --from=markdown --to=native derivation/runs/C2/CITATION_BRIEF.md
```

上述检查均通过。
