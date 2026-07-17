# M07 FIRST RELEASE INTEGRATION 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M07_FIRST_RELEASE_INTEGRATION_REQUIREMENTS

本窗口只讨论并冻结 M07 FIRST RELEASE INTEGRATION（首版完整无实验数据合成实验）的需求。不得编码，不得在集成层发明新物理。

首版完成含义是：M00–M05 能从配置独立生成 A/B 合成实验结果，M06 能在另一个只读进程中消费结果并出图。正式 C 偏心加载不是本任务范围。

开始前完整读取：
1. AGENTS.md、README.md、theory/README.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00–M06 requirements 和全部 output contracts；
4. 所有已生成的 output change requests 及其处理状态；
5. theory/evidence_reassessment/README.md 与 theory/evidence_reassessment/engineering_fixed_context.md；
6. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
7. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
8. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
9. theory/system/SYSTEM_INTEGRATED_MODEL.md 的依赖、输出、验证和实现交接章节。

前置要求：M00–M06 需求必须 frozen。若源模块存在尚未决定的 breaking 输出缺口，先报告阻断，不在 M07 静默解决。

讨论方式：
- 先提出一个小而完整、运行时间可控的 baseline experiment；
- 每轮最多问 3 个关于首版设计矩阵、运行预算、交付形式或验收的问题；
- 依次讨论“完整实验矩阵”“单一运行入口/环境”“结果与绘图交付”“回归/性能”“失败与完成定义”；
- 集成需求只能连接已冻结模块，新增物理需求必须退回所有者模块。

本窗口必须关闭的问题：
1. 一个文档化入口怎样生成 resolved config、surface、A/B cases、result bundle；
2. baseline 中的解析表面、合成表面、seed 和设计对照；
3. 单刺、2×5/5×2、rigid/spring 以及至少两个设计因素的最小覆盖；
4. 哪些 case 跑完整 100 mm，哪些只能作为明确标记的调试 fixture；
5. 至少一个预期 unavailable/失败 case 的分类验证；
6. 首版 smoke 的时间、内存、磁盘预算和超时策略；
7. 中断恢复、case 级失败隔离和重放；
8. raw/event/summary/manifest 的完整性门；
9. M06 作为独立命令/进程读取既有 bundle 的验收；
10. 基线图清单与 plot manifest；
11. 删除绘图依赖后仿真仍运行、删除求解器依赖后绘图仍读取的隔离测试；
12. step/surface/seed 精化的最小数值证据；
13. DEV_PRIOR/synthetic_surface/no_damage/not_certifiable 的强制标签；
14. README、示例配置、运行说明和结果解释边界；
15. “首版完成”与 future backlog 的准确清单。

硬边界：
- 不实现 C 非零 +X、45°、rocking 或 Fcrit；
- 不在集成层复制或改写 surface/A/B；
- 不用 mock 结果冒充完整 case；
- 不因个别 case 失败而删除记录或补零；
- 不把所有设计组合一次性穷举作为首版门槛；
- 不要求任何实验文件；
- 不把一张图成功生成当作物理/数值验证完成。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M07_FIRST_RELEASE_INTEGRATION_REQUIREMENTS.md；
2. 冻结 baseline matrix、运行入口、结果/图形交付、性能和完整验收；
3. 生成 docs/simulator_development/implementation_prompts/M07_FIRST_RELEASE_INTEGRATION_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验所有模块依赖单向、输出字段可用和 C 边界；
5. 提交推送并报告后停止。

不得在本窗口集成或运行正式实验。
```
