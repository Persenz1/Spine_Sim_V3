# A2-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-16`  
> 接受版 SHA-256：`09ca48fdd68779005ad504c722538bfce477b0b60cf4ee554295f4a85366ce6a`

## 产物与归档

- 四个网页下载原件均已按下载文件名原样保存到 `derivation/runs/A2/raw_downloads/`，逐文件字节数和 SHA-256 与接收源一致。
- 规范化候选分别保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md`；候选内容与对应原件逐字一致。
- `RAW_RESPONSE.md` 保存本轮随附件收到的完整文本消息。
- 通过审查的接受版已更新为 `derivation/modules/A/current/A_MODULE_CONTEXT.md`，并保存等字节历史快照 `A_MODULE_CONTEXT_after_A2.md`。
- `CITATION_BRIEF.md` 仅在 A2 运行目录归档，不进入后续默认上传链。

## 输入与运行身份

- 运行身份为 `A2-r01`，实际目录为 `derivation/runs/A2`；提示词、输入清单和十个上传路径顺序一致。
- 当前滚动 `A_MODULE_CONTEXT.md` 已升级到 A2，因此 A2 网页执行时的 A1 输入不再要求与当前工作区同哈希；复验从 `INPUT_MANIFEST.yaml` 冻结提交 `9cd3a1f0943bcbd340fdb472d2a40c911978903b` 读取旧输入。
- 冻结提交中十个输入的字节数和 SHA-256 全部匹配；文献 01、07 压缩包结构与 CRC 通过。

## 工程事实

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 逐字一致，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`。
- `RUN_UPDATE_SUMMARY.yaml` 可解析，`operation: none` 条目的空字段、证据列表、审批标志及运行身份符合合同。
- 没有机理方程进入工程事实候选，没有工程事实变化，也没有需要人工审批的工程范围、数值、坐标、边界、开关或未决项变化。
- 工程事实生成器校验通过：9 个领域、48 条事实。

## 模块完整性与边界

- A1 的第 1–12 节及附录 A–B 除文件头版本信息外逐行保留；A2 从第 13 节追加，形成 A1+A2 最新完整上下文。
- A2 的九类必答结果均有明确落点：自由度与功共轭、变形接触运动学、Signorini—Coulomb 二阶锥互补、三种结构柔顺、单边弹簧与硬限位、恒法向推力混合边界、非光滑求解、反力增长、验证及 A3/B 接口。
- `0.5 N` 始终作为全局 `-Z` 法向执行器主动推力，没有被写成局部接触法向力；切向位移控制对应的驱动反力和功方向闭合。
- 实际滑移迁移、材料失效、多刺共同平衡、载荷重分配和整爪力矩均保留给 A3/B/C，没有越界定义。
- 摩擦系数、接触刚度、高碳钢材料参数、弹簧采样点、梁升级阈值和数值容差均保持参数化或未决。

## 无歧义修复与公式核验

- 接受版文件头已规范为版本 `0.2.0`、状态 `accepted`。
- 原候选的二维单支持特例正确给出沿 $+\boldsymbol\tau$ 滑移的载荷比，但“分母非正”的说明未显式写出摩擦锥另一侧。接受版补入由 $|\lambda_t|\le\mu\lambda_n$ 唯一确定的下界，并明确该方向自锁只表示没有有限上侧滑移界，不代表任意小载荷都可行。
- 可复现数值检查覆盖：SOC 锥成员与正交、二维两个摩擦锥面、分母非正自锁分支、三维圆截面悬臂柔顺矩阵对称正定，以及接触点柔顺正性；全部通过。
- Markdown 数学块和代码围栏闭合，接受版与历史快照逐字一致。

## 引用核验

- `CITATION_BRIEF.md` 的 6 项顺序引用全部在正文使用且均有定义；本地文献只写“文献01/07”，GPT 通用知识说明了实际内容和适用边界。
- 三个外部直接网址于 `2026-07-16` 均可访问：Kanno 的三维准静态 Coulomb 接触/SOC 互补论文、SIAM 三维 Coulomb 接触原始—对偶活动集论文、MIT Euler–Bernoulli 梁官方讲义。
- 外部来源只支持数学与数值方法，没有被用来固定本项目材料参数、摩擦系数、接触刚度或容差。

## 可复现校验

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/A2/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/A2/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

三条命令均已通过。需要求解器代码、材料数据或实验输入的事件收敛、EB/Timoshenko 对比和参数标定继续作为 A2 上下文中的显式未决验证，不伪装成已完成数值事实。
