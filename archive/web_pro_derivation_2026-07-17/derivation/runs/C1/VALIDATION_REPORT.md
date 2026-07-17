# C1-r01 验证报告

> 结论：`pass / accepted`
> 处理日期：`2026-07-16`
> 接受版 SHA-256：`daa5702355fb56cf98cdd8194717fbe8e2b41311c9fd0ef29010484bd5f8654c`

## 产物与归档

- 四个网页下载原件已按浏览器实际文件名原样保存到 `derivation/runs/C1/raw_downloads/`，逐文件字节数和 SHA-256 已写入 `INPUT_MANIFEST.yaml`。
- 规范化候选保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml`、`RUN_UPDATE_SUMMARY.yaml` 和 `CITATION_BRIEF.md`；全部与对应下载原件逐字节一致。
- `RAW_RESPONSE.md` 保存本轮随四个附件收到的完整网页文本回答；原始下载和完整回答受 `.gitattributes -text` 规则保护。
- 接受版已更新为 `derivation/modules/C/current/C_MODULE_CONTEXT.md`，并保存等字节历史快照 `derivation/modules/C/history/C_MODULE_CONTEXT_after_C1.md`。
- `CITATION_BRIEF.md` 只在 C1 运行目录归档，不进入下一任务上传链。

## 输入、运行身份与前置继承

- 运行身份为 `C1-r01`，实际目录为 `derivation/runs/C1`；正式提示词、输入清单和 10 个上传路径的数量、顺序、字节数与 SHA-256 一致。
- 冻结提交 `71fbd336ef514b4346b37d6e3dd8d599531183b4` 中的全部网页输入与 `INPUT_MANIFEST.yaml` 一致；正式提示词与运行归档副本逐字节一致。
- `B_INTEGRATION-r01` 输入和产物验证重新通过；`B_INTEGRATED_MODEL 1.0.0 accepted` 与 `B_TO_C 1.0.0 accepted` 的身份和哈希一致。
- 文献 09、20 压缩包均只包含完整 `evidence_card.md` 和三幅关键图，CRC 通过；没有把备用文献 07、17、28 混入本轮证据链。
- C1 是 C 模块首阶段，网页执行时没有既有 C 上下文；当前接受版为 `C_MODULE_CONTEXT 0.1.0 accepted`。

## 工程事实与运行摘要

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 逐字节一致，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`。
- `RUN_UPDATE_SUMMARY.yaml` 可解析；运行身份、`operation: none`、空证据列表、`proposed_fact: null` 和 `approval_required: false` 符合无变化合同。
- 工程事实生成器通过：9 个领域、48 条事实。坐标、几何、工况、扫描边界、模型开关、损伤边界、首版范围和未决登记均未变化，无需人工审批工程事实。

## C1 语义与物理闭合

- 四个静态右手安装基、工程参考点 `O_i`、B 规范参考点 `O_A` 及到全局参考点 `C` 的版本化偏置和运输关系完整；力、力矩、twist 和功不变条件闭合。
- 四个单元严格共享唯一径向坐标 `s`；各自的法向位置、contact-only wrench、活动/承载状态、事件、损伤、行程和能力仍独立，未把同步位移误写成同步反力。
- 共同驱动广义反力由虚功得到；对称对置分支可以全局面内合力为零，同时保持非零内部预紧和非零驱动反力。异质分支的对置不平衡与完整 contact-only 残量均单列。
- `P_i` 每单元只作为 B 外层恒法向主动广义推力出现；未除以针数，且未与径向控制、横向/转动约束反力一起重复加入墙面 contact-only wrench。
- `embedded_array_unit_trial` 是唯一 B 物理入口；`UX_PZ_BALANCED`、`PRESCRIBED_XZ_RESIDUAL`、graph 非唯一性、局部切线 trust region 和完整回调边界均按 `B_TO_C 1.0.0` 继承。
- 全局最早事件采用四单元最小事件分数；缩步后四单元从同一接受快照重调，未缩放旧 wrench、旧 `u_z` 或旧损伤意图。单元内部事件组、跨单元同时事件、共享 DamageStore fixed point、同位置级联和功账本均保留。
- 四单元、内部 A、共享 DamageStore、事件和能量账本采用 prepare 后一次全局原子提交；任一失败全部回滚，重复幂等键不重复累计历史。
- 正常停止同时门控能力平台、乐观边际收益、最弱分支、安全/损伤/强度/行程/碰撞/认证和保持窗口；上限未达标、安全停止、不可恢复、未认证和数值停止均与正常停止分离。
- 阈值、能力特征、统计规则和 `s_max` 保持待标定；未把 B 层 100 mm 或文献机构数值硬编码为 C1 参数。
- `C1PreloadState` 完整冻结共同径向位置并继承 B/A opaque 历史、共享 DamageStore、事件、行程、能力、版本和提交收据；法向平衡及低层历史仍只通过合法 B/A trial 演化。
- 当前 B 合同不认证真实 rocking；接受版明确拒绝旋转旧 wrench 或投影旧状态伪装支持。C2 偏心平衡/rocking 与 C3 渐进失效/最大承载均未提前完成。

## 引用核验

- `CITATION_BRIEF.md` 的 4 项顺序引用均在正文使用且有定义；本地来源只写“文献09/20”，GPT 通用知识说明了内容和适用边界。
- Northwestern University 的 [Modern Robotics 第 3 章](https://modernrobotics.northwestern.edu/chapters/chapter3/) 页面可访问，并明确覆盖 SO(3)/SE(3)、twist、adjoint 和 wrench 表达变换；本轮只将其用于坐标/功对偶交叉检查，没有从外部资料引入工程数值。
- 文献 09 只支持对置预紧、柔顺/限位权衡和再挂接结构；文献 20 只支持中心同步径向搜索、分层柔顺、挂接后增载和释放顺序。独立刺假设、16 车架运动、岩石拉脱值和论文机构参数均未升级为项目事实。

## 机械修复与可复现验证

- 浏览器后缀 `(6)` 只在规范化文件名中移除；四份网页内容均无需公式、YAML、路径或模板修复。
- 接受版相对候选只把文件头状态 `candidate` 更新为 `accepted`；正文技术语义不变，current 与 C1 历史快照逐字节一致。
- 解析代理验证了四个旋转矩阵的正交性和右手性、80 mm 对置间距、非零参考点偏置下 wrench–twist 功不变、对称预紧零合力/非零驱动反力以及异质分支不平衡。
- 最早/同时事件集合对单元枚举顺序不变；失败 prepare 不污染共同坐标、四单元状态、DamageStore 或事件号；弱分支不足或边际收益仍高时联合停止门槛为假。
- `C_MODULE_CONTEXT` 的 0–15 级主章节、28 项验证矩阵、代码围栏、显示数学块、必需状态码、模板残留和 C2/C3 边界检查通过；current、候选和引用说明均通过 Pandoc Markdown 解析。
- 工程事实正式基线未改动；没有需要人工决定的工程事实或物理机理冲突。

## 可复现命令

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C1/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/C1/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
pandoc --from=markdown --to=native derivation/modules/C/current/C_MODULE_CONTEXT.md
pandoc --from=markdown --to=native derivation/runs/C1/MODULE_CONTEXT_CANDIDATE.md
pandoc --from=markdown --to=native derivation/runs/C1/CITATION_BRIEF.md
```

上述检查均通过。需要真实 B/C 实现、真实 CAD、材料/表面参数、损伤协调器、停止策略数据、统计留出或目标实验的检查继续作为接受上下文中的显式未决验证；本次接受不把理论合同完成伪装为代码或实验完成。
