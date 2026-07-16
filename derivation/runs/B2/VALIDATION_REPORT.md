# B2-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-16`  
> 接受版 SHA-256：`65aeb65e28887942b8eed9e95d7339d62604b52000f2b6133def7245513dae22`

## 产物与归档

- 四个网页下载原件均按浏览器实际文件名原样保存到 `derivation/runs/B2/raw_downloads/`，逐文件字节数和 SHA-256 已写入 `INPUT_MANIFEST.yaml`。
- 规范化候选保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md`；四份候选均与对应原件逐字节一致。
- `RAW_RESPONSE.md` 原样保存本轮随附件收到的文本回答 `四个生成`（文件中不添加解释性内容）。
- 接受版已更新为 `derivation/modules/B/current/B_MODULE_CONTEXT.md`，并保存等字节历史快照 `derivation/modules/B/history/B_MODULE_CONTEXT_after_B2.md`。
- `CITATION_BRIEF.md` 只在 B2 运行目录归档，不进入 B3 默认上传链。

## 输入、运行身份与前置继承

- 运行身份为 `B2-r01`，实际目录为 `derivation/runs/B2`；提示词、输入清单和 12 个上传路径的数量、顺序、字节数与 SHA-256 一致。
- 冻结提交 `fa697ad7eb643c262ce958ae5e398c2cc8099800` 中的全部网页输入与 `INPUT_MANIFEST.yaml` 一致；正式提示词与运行归档副本逐字节一致。
- B1-r01 接受报告、B1 历史快照、A_TO_B 1.0.0 accepted 合同和冻结输入复验通过；B1 第 2–15 节、16.1 起的交接正文及第 17 节审计结论在 B2 接受版中逐字保留。
- 文献 06、07、10 压缩包均包含 `evidence_card.md` 和三幅关键图，CRC 通过。

## 工程事实与运行摘要

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 逐字节一致，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`。
- `RUN_UPDATE_SUMMARY.yaml` 可解析；运行身份、`operation: none`、空证据列表、`proposed_fact: null` 和审批标志符合无变化合同。
- 工程事实生成器通过：9 个领域、48 条事实。没有固定数值、扫描集合、坐标、边界、模型开关、首版范围或未决登记变化，无需人工审批工程事实。

## B2 语义、力学闭合与边界

- 接受版是 B1+B2 最新完整上下文：给定共同切向位置或增量和每单元主动法向推力，以 `u_z` 为唯一外层位移未知量；唯一分支使用标量残量，刚性/退化分支保留 admissible wrench graph 和集合值平衡。
- 每单元 `P_z` 只在 B2 外层施加一次；A_on_B 接触 wrench、主动执行器力、x 位移控制反力以及 y/转动约束反力分开记账，功方向与共同参考点运输一致。
- 几何接触、实际承载、粘滑、安装结构、材料/针体事件、求解质量和唯一性保持正交；开放针在共同位置改变后重新调用，错误或不可用响应不得伪装为零承载。
- 刚性安装与独立轴向弹簧使用同一外层框架；弹簧无拉力、4 mm 硬限位和柔顺去重保持工程事实语义，刚性集合值反力不由任意大有限罚刚度替代。
- 逐针 wrench/线性化到单元原始线性化、法向残量斜率和恒 `P_z` 凝聚切线闭合；奇异、事件或集合值分支不会被伪装为普通唯一切线。
- 外层算法从同一接受状态进行无副作用全阵列试探，采用保护的半光滑/广义 Newton 或回退方法；共同事件取最小步长分数并在缩短后的共同切向位置重新求法向平衡。
- 预载继续搜索、平衡唯一、平衡退化、事件减步、B3 交接、几何/碰撞/域/硬限位不可行、物理无解、数值未收敛、模型缺失和合同错误均分别分类。
- 四个必答现象均有可计算链：名义刺数不保证实际承载增加；`2×5` 与 `5×2` 保持方向差异；弹簧存在依赖工况的过硬/过软窗口；相同总主动推力不隐含逐针均载。
- B2 只返回无副作用 `B2EquilibriumTrial` 和 `B3_REBALANCE_REQUIRED` 交接；没有执行失效后重分配、共享损伤提交、连续再挂接、完整 100 mm 历史、B 集成或 C 层任务。

## 引用核验

- `CITATION_BRIEF.md` 的 7 项顺序引用均在正文使用且有定义；本地来源只写“文献06/07/10”，GPT 通用知识说明了内容与边界。
- DOI `10.1007/BF01581275` 对应 Qi 与 Sun 的非光滑 Newton 方法论文；DOI `10.1137/S1052623401383558` 对应 primal-dual active set 与 semismooth Newton 等价论文。
- PETSc 官方 SNES 文档明确列出带盒约束变分不等式的 reduced-space active-set 和 semismooth Newton 求解器；接受版仅把这些资料作为数值组织参考，没有据此替代 A 层接触/材料本构或承诺当前问题全局唯一。
- 文献 06/07/10 的样机数值、材料、回差、机构和区域斜率均保留迁移边界，没有升级为本项目固定工程参数。

## 机械修复与可复现验证

- 仅执行浏览器重名规范化、候选到接受状态同步、文件末尾空行规范化、运行后冻结输入复验和原件字节保护；所有变更记录在 `MECHANICAL_FIXES.md`。
- `.gitattributes` 对运行目录中的 `raw_downloads` 和 `RAW_RESPONSE.md` 禁用文本换行转换；四个原件及完整文本回答的工作副本、Git 索引和清单 SHA-256 一致。
- 解析代理验证了共同位移下部分接触与不均载、针调用顺序不变性和 `N_eff` 边界；合成光滑分支验证了恒 `P_z` Schur 凝聚切线与中心差分一致。
- 共同事件最小分数及同时事件集合对调用顺序不变；主动推力与接触 Z resultant 平衡；弹簧压缩保持在 `[0,4] mm` 且不产生拉力。
- Markdown 代码围栏、显示数学块、章节、标记和引用闭合；接受上下文与引用说明均通过 Pandoc Markdown 解析。
- 当前 B 上下文与 B2 历史快照逐字节一致；工程事实正式基线未改动。

## 可复现命令

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B2/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B2/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
pandoc --from=markdown --to=native derivation/modules/B/current/B_MODULE_CONTEXT.md
pandoc --from=markdown --to=native derivation/runs/B2/CITATION_BRIEF.md
```

五项检查均通过。需要真实 A 实现、真实 CAD、材料/表面参数、求解器容差、自动测试实现或实验数据的检查继续作为 B2 接受上下文中的显式未决验证；本次接受不把规范完成伪装为代码或实验完成。
