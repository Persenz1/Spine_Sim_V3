# A3-r01 验证报告

> 结论：`pass / accepted`  
> 处理日期：`2026-07-16`  
> 接受版 SHA-256：`cca6febc359cf30f2c0454e375f010222da5c642b43316bb7a5f712cdf2da898`

## 产物与归档

- 四个网页下载原件均按下载文件名原样保存到 `derivation/runs/A3/raw_downloads/`，逐文件字节数和 SHA-256 与接收源一致。
- 规范化候选保存为 `MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md`；所有机械修复均有原件和 `MECHANICAL_FIXES.md` 可追溯。
- `RAW_RESPONSE.md` 保存本轮随附件收到的完整文本消息。
- 接受版已更新为 `derivation/modules/A/current/A_MODULE_CONTEXT.md`，并保存等字节历史快照 `derivation/modules/A/history/A_MODULE_CONTEXT_after_A3.md`。
- `CITATION_BRIEF.md` 只在 A3 运行目录归档，不进入后续默认上传链。

## 输入与运行身份

- 运行身份为 `A3-r01`，实际目录为 `derivation/runs/A3`；提示词、输入清单和 12 个上传路径的数量、顺序、字节数与 SHA-256 一致。
- 当前滚动 `A_MODULE_CONTEXT.md` 已升级到 A3，因此网页执行时的 A2 输入从 `INPUT_MANIFEST.yaml` 冻结提交 `22a166cf926d104bddf3ca9c377b26d69e0ea3b4` 复验，不要求升级后的工作区继续保持旧哈希。
- 冻结提交中的 12 个输入全部匹配；文献 03、05、14、15 压缩包均包含 `evidence_card.md` 和三幅关键图，CRC 全部通过。

## 工程事实

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 逐字一致，SHA-256 均为 `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb`。
- `RUN_UPDATE_SUMMARY.yaml` 可解析，运行身份、`operation: none`、空字段、证据列表和审批标志符合模板；没有生成器不渲染的隐藏字段。
- 没有机理方程进入工程事实，没有固定数值、扫描集合、坐标、边界、模型开关、首版范围或未决登记变化。
- 工程事实生成器校验通过：9 个领域、48 条事实。本轮不需要人工审批工程事实。

## 模块完整性、语义和边界

- 候选除文件头滚动信息外，逐行完整保留 A2 接受版的第 1–25 节及附录；A3 从第 26 节追加，形成 A1+A2+A3 最新完整上下文。
- A3 十类必答结果全部有明确落点：真实滑移提交、三维球尖迁移、释放/再挂接、局部材料容量与尺度桥接、针体强度、不可逆损伤、完整状态机、并发事件、耦合残量/伪代码、连续 `100 mm` 多峰输出和 A→B 单刺接口。
- 首版明确选择“有限控制体应力域 + 不可逆能量正则化软化”；几何特征结果量容量仅作为有直接单刺标定时的显式备选。该选择符合提示词要求，未硬编码目标材料参数。
- `0.5 N` 仍是全局法向执行器主动推力；A2 的 SOC 最大耗散、梁/弹簧柔顺、无拉力原长端、`4 mm` 硬限位和体碰撞优先级均未改写。
- 损伤层不修改 A1 原始表面；多针共同平衡、载荷共享、整爪平衡、显式裂纹/碎屑、重网格化和磨损均保持越界禁止。
- 材料核尺度、方向/压力敏感强度、混合模态断裂能、残余容量、砂纸分支、针体牌号/强度、搜索控制路径和数值容差全部保留为待标定或显式模型选择。
- 未发现需要人工取舍的实质语义冲突；A3 的完成只表示机理、状态、算法和接口规范闭合，不伪装为代码、材料标定、收敛或实验验证已完成。

## 无歧义修复与公式核验

- 接受版文件头已从 `candidate` 规范为 `accepted`，版本保持 `0.3.0`。
- 为候选已声明但未定义的 `moment_augmented` 可选分支补入通用无量纲力矩利用率接口，并明确无标定时关闭；参数表符号统一到正文的 `\mathbf R_{m,k},\mathbb H_k`。未选择容量函数或新增参数值。
- 不稳定的 Northwestern 作者副本地址替换为同一 Bažant–Oh 论文的 Springer 官方出版页；证据身份、用途和边界未变化。
- 可复现数学检查覆盖：有限控制体应力代理的牵引一致性、Mohr–Coulomb 归一化面、线性软化端点与完整耗散 `A G_c`、损伤投影 KKT、球尖纯滚动零滑移、圆截面惯性矩和组合应力上界；全部通过。
- Markdown 数学块、代码围栏和方程标签闭合且标签唯一；接受版与 A3 历史快照逐字一致。

## 引用核验

- `CITATION_BRIEF.md` 的 7 项顺序引用全部在正文使用且均有定义；本地文献只写“文献03/05/14/15”，GPT 通用知识明确说明实际内容和适用边界。
- Bažant–Oh 官方出版页 `https://link.springer.com/article/10.1007/BF02486267` 可访问，并直接支持 crack-band 的特征宽度、断裂能和网格客观性用途。
- NASA 技术报告 `https://ntrs.nasa.gov/api/citations/20020053651/downloads/20020053651.pdf` 可访问，并直接支持单一不可逆损伤变量、混合模态软化及卸载不恢复黏聚状态的结构。
- 外部来源只用于通用正则化/黏聚结构，不提供目标红砖、混凝土、砂纸或针体的批准数值。

## 可复现校验

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/A3/validate_inputs.py
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/A3/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

三条命令均通过。需要求解器代码、目标材料/针体数据或实验输入的事件收敛、损伤核/网格客观性、搜索控制器对应和多峰回归继续作为 A3 上下文中的显式未决验证。
