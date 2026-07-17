# B3-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-16`  
> 接受版 SHA-256：`35e072fc730e2e74edc1d2c3cdc392382566b0b9ee2a2edd4947585038c4bc21`

## 产物与归档

- 四个网页下载原件已按浏览器实际文件名原样保存到 `derivation/runs/B3/raw_downloads/`，逐文件字节数和 SHA-256 已写入 `INPUT_MANIFEST.yaml`。
- 规范化候选保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md`。除模块上下文的一处 LaTeX 转义机械修复外，其余三份与原件逐字节一致。
- `RAW_RESPONSE.md` 保存本轮随四个附件收到的完整网页文本回答；原始下载和完整回答受 `.gitattributes -text` 规则保护。
- 接受版已更新为 `derivation/modules/B/current/B_MODULE_CONTEXT.md`，并保存等字节历史快照 `derivation/modules/B/history/B_MODULE_CONTEXT_after_B3.md`。
- `CITATION_BRIEF.md` 只在 B3 运行目录归档，不进入下一任务上传链。

## 输入、运行身份与前置继承

- 运行身份为 `B3-r01`，实际目录为 `derivation/runs/B3`；正式提示词、输入清单和 12 个上传路径的数量、顺序、字节数与 SHA-256 一致。
- 冻结提交 `f5e910fa72d6b9c26c7fee37b4beb9f3c05fb962` 中的全部网页输入与 `INPUT_MANIFEST.yaml` 一致；正式提示词与运行归档副本逐字节一致。
- B2-r01 接受报告、B2 历史快照、`A_TO_B 1.0.0 accepted` 合同和冻结输入复验通过；网页实际上传的 B 模块基线为 `0.2.0 accepted`。
- B3 候选第 2–16、18–30 节与 B2 接受快照逐字一致；第 17 节只更新当前总自检的交叉引用；第 31–33 节只增加“历史基线”说明，B2 正文和自检条目保持不变。
- 文献 03、09、21 压缩包均包含 `evidence_card.md` 和三幅关键图，CRC 通过。

## 工程事实与运行摘要

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 逐字节一致，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`。
- `RUN_UPDATE_SUMMARY.yaml` 可解析；运行身份、`operation: none`、空证据列表、`proposed_fact: null` 和 `approval_required: false` 符合无变化合同。
- 工程事实生成器通过：9 个领域、48 条事实。坐标、几何、工况、扫描边界、模型开关、损伤边界、首版范围和未决登记均未变化，无需人工审批工程事实。

## B3 语义、事务和力学闭合

- 接受版是 B1+B2+B3 最新完整上下文，覆盖全阵列事件后重平衡、共同平衡自动重分配、同时事件与同位置级联、共享 DamageStore 冲突协调、回滚和全局原子提交。
- 失效前后均在相同 `u_x` 和恒定单元 `P_z` 下重新调用全部针并重求共同 `u_z`；没有使用失效针旧载荷包、固定邻居权重、局部/全局共享替代模型或“有效刺数×平均单刺力”。
- 同时事件组、四种试探相位、损伤读写冲突图、受影响闭包、fixed-point 级联、Zeno 防护、陈旧快照、幂等键及 prepare/commit/rollback 边界闭合；真实非唯一性保留 graph/分支集合，不按针 ID 选解。
- 释放针保留 continuable/terminal 区分、结构回弹、`0–4 mm` 弹簧压缩与剩余行程、硬限位进入/离开、持续搜索和再挂接；全局路径和时间不重置。
- 100 mm 事件驱动接受历史、`1 mm/s` 时间映射、逐针/单元/事件原始量、外功—储能—耗散账本和确定性重放要求完整。
- `UnitCapabilityState` 仍明确为历史相关候选接口；低维切线/graph 只在固定分支、损伤版本不变和 trust region 内有效，跨事件或质量不足时强制完整针级回调。
- 物理无解、物理失稳、可恢复/不可恢复脱附、退化、数值不收敛、参数/模型缺失、域外、体碰撞、陈旧快照和损伤事务冲突分别分类。
- 九个 B3 必答问题和理论结果均在第 34–49 节形成，第 48 节逐项映射；第 50 节确认未执行 B 集成、未生成 `B_TO_C_CONTRACT`、未开始 C1。

## 引用核验

- `CITATION_BRIEF.md` 的 7 项顺序引用均在正文使用且有定义；本地来源只写“文献03/09/21”，GPT 通用知识说明了内容和适用边界。
- SUNDIALS IDA 官方数学说明确认多根函数检查、符号变化括区间和改进割线根定位，并明确偶重根可能遗漏；B3 仅将其用作事件定位参考，不把准静态问题改写为 ODE/DAE。
- PETSc 官方 SNES 文档确认盒约束变分不等式可使用 reduced-space active-set 与 semi-smooth Newton 求解器；B3 仅将其用作非光滑数值组织参考，不替代 A 的接触、摩擦、硬限位或材料物理。
- PostgreSQL 官方 `PREPARE TRANSACTION`/`COMMIT PREPARED` 文档确认两阶段准备、提交或回滚语义；B3 只作软件事务类比，项目状态所有权、令牌、版本和原子性仍以 `A_TO_B 1.0.0 accepted` 为唯一权威。
- 三个官方直接来源均可访问；文献样机的刚度、预载、力界、0–2 mm 跳峰和约 5 mm 趋势均未升级为项目固定参数。

## 机械修复与可复现验证

- 唯一网页内容修复是把第 44.4 节损坏的制表符 `ext{branch/history}` 恢复为 LaTeX `\text{branch/history}`；原件不变，完整关系记录在 `MECHANICAL_FIXES.md`。
- 解析代理验证了失效针移除后恒 `P_z` 的全阵列重平衡、事件前后法向力差量闭合、其余针载荷变化和针调用置换不变性。
- 冲突图连通分量对边方向/枚举不变；失败的准备事务不污染接受路径、逐针版本、DamageStore、耗散或事件号。
- 共同最早事件和同时事件集合对枚举顺序不变；弹簧压缩保持在 `[0,4] mm`；100 mm 路径对应 100 s；法向主动推力功方向检查通过。
- Markdown 的 1–50 级主章节、代码围栏、显示数学块、必需状态码、模板残留和引用闭合检查通过；current、候选和引用说明均通过 Pandoc Markdown 解析。
- 接受版与 B3 历史快照逐字节一致；工程事实正式基线未改动。

## 可复现命令

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B3/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/B3/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
pandoc --from=markdown --to=native derivation/modules/B/current/B_MODULE_CONTEXT.md
pandoc --from=markdown --to=native derivation/runs/B3/MODULE_CONTEXT_CANDIDATE.md
pandoc --from=markdown --to=native derivation/runs/B3/CITATION_BRIEF.md
```

六项检查均通过。需要真实 A 实现、真实 CAD、材料/表面参数、损伤协调器、刚性 admissible graph、求解器容差、长程回归或实验趋势的检查继续作为接受上下文中的显式未决验证；本次接受不把理论合同完成伪装为代码或实验完成。
