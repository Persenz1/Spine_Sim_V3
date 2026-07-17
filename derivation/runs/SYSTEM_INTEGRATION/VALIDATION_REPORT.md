# SYSTEM_INTEGRATION-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-17`  
> 网页原件/候选副本 SHA-256：`97727736147dcffbe530ecbeaf0c929faca524cf90a3c2aad42fd05a328e5802`  
> 正式系统模型 SHA-256：`8600f4fefb0d779e6a7a8cffd9212f8570d5108864f3db56475be8285f5db91f`

## 产物、归档和接受边界

- 网页下载原件按原始字节保存在 `derivation/runs/SYSTEM_INTEGRATION/raw_downloads/SYSTEM_INTEGRATED_MODEL.md`；候选副本与原件逐字节一致。`RAW_RESPONSE.md` 保存本轮仅附件交付的响应标记。
- 运行身份为 `SYSTEM_INTEGRATION-r01`，实际目录为 `derivation/runs/SYSTEM_INTEGRATION`，没有覆盖历史。五个输入仍由冻结 Git 提交、逐文件字节数和 SHA-256 复现。
- 正式接受版写入 `derivation/system/SYSTEM_INTEGRATED_MODEL.md`。候选到接受版的全部差异均列入 `MECHANICAL_FIXES.md`，没有回写原件或候选副本。
- 本轮没有生成子模块式工程事实候选、`RUN_UPDATE_SUMMARY.yaml` 或 `CITATION_BRIEF.md`，也没有启动任何后续任务。

## 全局机理闭合结论

- **理论/规范依赖链闭合。** 表面实现 → A 单刺本征核 → B 阵列共同平衡/事件/损伤 → C 同步预紧与偏心理论 → 系统原始输出形成单向依赖；低层所有权没有被系统层重定义。
- **当前在线合同闭合到 A/B standalone 与 C 的 x/Z 同步预紧路径。** C 自动形成合格锁定态仍要求外部提供并认证停止策略、阈值和 `s_max`。
- **正式非零偏心路径尚未合同在线闭合。** `B_TO_C 1.0.0 accepted` 不支持局部 y、真实转动、动态姿态或完整 twist；非零 `+X`、`45°` 和 rocking 必须在任何低层物理调用前返回 `C_CONTRACT_EXTENSION_REQUIRED`，并保持 accepted state、δP、A/B、`DamageStore`、事件、功、曲线、峰值和 `F_crit` 零推进。该状态不是零承载或物理失败。
- B 2.x 只作为 `required extension / not accepted` 保存；解除阻断需要版本化完整 twist/动态几何/6D graph、B 1.0 向后兼容及功、事件、损伤、事务和验证证据正式通过。

## 工程事实与 A→B→C 接口

- 工程事实 `1.0.0`、A/B/C `1.0.0 accepted`、A→B/B→C `1.0.0 accepted` 的身份、状态和输入哈希一致；A→B、B→C 嵌入标记块分别与独立正式合同逐字一致。
- A embedded 只接受 B 规定的基座运动和 accepted/损伤快照，不接受逐针恒推力；B 外层仅施加一次每单元 `P_i`，C 不重复加入 contact-only 墙面 wrench。
- `SystemAcceptedState` 以 C accepted state 为唯一物理当前状态，并用同一原子收据绑定四个 B、全部 A opaque states、一个共享 `DamageStore` 以及事件、功、曲线和峰值账本，没有第二份可修改低层状态。
- A/B standalone 与 C 系统主路径共享相同低层核，但请求 schema、运行 ID、accepted history 和 `DamageStore` 分支互相隔离。

## 坐标、单位、力、功和物理去重

- 全局/单元/针/接触坐标、`O_i`、`O_Ai`、C、P、非零参考点偏置、刚体变换和 wrench 运输均有唯一表达；B 响应源坐标和变换版本不得靠名称推断。
- mm、N、N·mm、rad、s、MPa 和 N/mm 的规范单位及 μm→mm、N/m→N/mm、deg→rad 的单一换算边界明确；N 与 N·mm 残量必须分块或使用版本化尺度，接受仍检查原始有量纲分量。
- `A_on_B`、B contact-only、`P_i`、x/横向/转动控制反力、共同径向驱动、偏心加载器和真实约束均分栏。作用—反作用、参考点运输和 wrench–twist 功不变回归通过。
- 球尖接触、摩擦、针梁、针级轴向弹簧/硬限位、材料损伤、针体强度、阵列共同平衡和 C 刚体平衡均只有一个物理所有者；外部功、层间端口审计、储能、耗散、释放能和数值误差没有重复计数。

## 状态、事件、历史、终止和原始输出

- accepted/trial/rollback/prepare/commit 形成全局原子事务；Newton、线搜索、事件定位、DamageStore fixed point、级联、回滚和幂等重试均不能推进永久历史。
- 致命认证状态、物理事件最早性、同时事件组、事件后一侧依赖偏序、跨单元共享损伤 fixed point、同位置级联和 Zeno 防护均完整；原始 A/B 事件不会被高层总 if/else 删除。
- 不可行或失稳 trial 不得作为 accepted 状态提交；终止证据绑定最后有效/合法边界状态。首针失效、首单元退化、首次下降、局部峰、整体峰、物理终止和 `F_crit` 确认互不等价。
- A/B 的 100 mm、1 mm/s accepted standalone 路径与 C 的 `s`、δP 和未固定时间严格分离。
- 单刺、阵列、同步预紧和未来获合同支持的偏心加载均保留逐 accepted 点、逐事件、逐针/逐单元、完整 wrench、路径、姿态、损伤、能量、质量、不确定性、版本、哈希和事务收据；原始曲线不会被峰值、滤波、评分或二元标签替代。

## 未决项和认证等级

- 当前没有需要用户在本轮决定的歧义语义冲突。模型中的未决项均保留安全处理、阻断阶段、责任层和客观关闭条件。
- 主要开放项是 B 2.x 完整运动合同、C 预紧停止策略/阈值/`s_max`、执行器端点与试验架边界、CAD/表面/材料/损伤参数、数值容差/稳定性/分支覆盖、统计样本和实验协议。
- `accepted` 只表示全局理论、接口和规范审查通过；实现、数值、参数标定、趋势验证和定量实验等级仍为未认证。

## 可复现验证

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/SYSTEM_INTEGRATION/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/SYSTEM_INTEGRATION/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

三条命令均已通过；`git diff --check` 也通过。SYSTEM_INTEGRATION 到此结束。
