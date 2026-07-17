# M06 PLOTTING 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M06_PLOTTING_REQUIREMENTS

本窗口只讨论并冻结 M06 PLOTTING（只读结果解析、动态绘图配方和派生数据）的需求。不得编码，不得运行任何仿真，不得导入或调用求解器，不得修改 canonical result bundle。

绘图模块的特殊定位：
- 它只读取既有数据和公共 ResultReader/API；
- 随模块与研究问题动态调整 recipe；
- 可以发现原始输出缺失，但只能形成 PLOT_DATA_GAP_REQUEST；
- 任何源数据增加必须回到数据所有者模块的新需求/实现窗口；
- 绘图模块不得成为仿真依赖图的一部分。

开始前完整读取：
1. AGENTS.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00–M05 requirements，重点读取所有 canonical output 和 plotting needs；
4. theory/system/SYSTEM_INTEGRATED_MODEL.md 第 25–30 节；
5. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
6. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
7. 仓库中现有结果 schema/API（若尚无实现，明确以冻结 requirements 为输入，不虚构已存在 API）。

讨论方式：
- 先汇总 M01–M05 已声明的基线图和现有字段覆盖；
- 对“必须图、调试图、论文图、可选探索图”分层；
- 每轮最多问 3 个关于出图内容、交互方式或导出规范的问题；
- 先判断图能否由已有 raw 字段派生，再讨论是否需要数据缺口请求；
- 图形样式参数必须与物理/实验参数分离。

本窗口必须关闭的问题：
1. ResultReader 的唯一读取入口和支持的 schema 版本；
2. recipe 的注册、参数、版本、依赖字段和适用模块；
3. case/design/seed/状态/事件的筛选、分组、分面和叠图；
4. 单运行路径图、事件局部图、多 seed 分布图、参数趋势图、排名图；
5. surface、numerics、A、B、experiment 的基线 recipe 清单；
6. 原始、派生、滤波、对齐和摘要字段的视觉标识；
7. 事件标记、状态带、置信区间和 unavailable 的表现；
8. 大结果按需读取、抽样仅用于显示、缓存和内存预算；
9. PNG/SVG/PDF/交互格式、尺寸、DPI、字体、中文、颜色与无障碍；
10. 调试主题、论文主题和批量导出目录；
11. plot manifest、source run hash、recipe/config hash；
12. derived artifact 的独立位置和失效缓存策略；
13. PLOT_DATA_GAP_REQUEST 的创建、去重、状态和回归测试；
14. 旧 schema、缺字段、损坏数据和部分完成运行的行为；
15. “删除求解器代码后仍能读取结果出图”的隔离验收。

逐模块至少讨论这些图：
- M01：高度/剖面/坡度/法向/PSD/分辨率；
- M02：残量/迭代/步长/事件括区/失败分类；
- M03：Rx-x/t、uz、状态带、局部接触、梁/弹簧、事件、功残量；
- M04：单元曲线、逐针热图、N*、不均载、余程、重分配、设计对比；
- M05：因素效应、分布、置信区间、seed 收敛、排名翻转、运行成本。

硬边界：
- 不 import surface/A/B/C/numerical solver 包；
- 不创建 trial 或调用 runner；
- 不把绘图时重新计算的物理量写回 canonical raw；
- 不用滤波曲线覆盖原始曲线；
- 不因缺字段猜测单位、frame、reference point 或状态；
- 不直接修改源模块输出；
- 不把绘图失败改写成仿真失败。

如果已有字段不足，按 REQUIREMENTS_DISCUSSION_WORKFLOW.md 输出完整 PLOT_DATA_GAP_REQUEST。能由现有 raw 无歧义得到的量应留在绘图 derived 层，不要求源模块重复保存。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M06_PLOTTING_REQUIREMENTS.md；
2. 冻结 reader 边界、recipe 系统、基线图、derived/manifest、缺口请求和验收；
3. 将本轮确认的数据缺口分别写成 docs/simulator_development/output_change_requests/<REQUEST_ID>.md，但不修改源模块；
4. 生成 docs/simulator_development/implementation_prompts/M06_PLOTTING_IMPLEMENTATION_WINDOW_PROMPT.md；
5. 校验没有仿真反向依赖；
6. 提交推送并报告后停止。

不得在本窗口实现绘图，也不得补跑仿真。
```
