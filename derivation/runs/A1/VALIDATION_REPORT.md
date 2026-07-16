# A1-r01 验证报告

> 结论：`pass`  
> 处理日期：`2026-07-16`  
> 接受版 SHA-256：`9a14d472e87bd9cb230abf1ad835cbf546771b38cdf5e797091dd02231821e9e`

## 产物与归档

- 11 个提示词输入全部存在，哈希与 `INPUT_MANIFEST.yaml` 一致；A1 最小文献包 01、11、12、16 完整。
- 四个网页输出均已原样保存；`RAW_RESPONSE.md` 单独保留网页回答。
- `MODULE_CONTEXT_CANDIDATE.md` 保留未经修改的原始候选。
- 通过审查的接受版与 `A_MODULE_CONTEXT_after_A1.md` 历史快照逐字一致。

## 工程事实

- `ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 `engineering_fixed_context 1.0.0` 逐字一致。
- `RUN_UPDATE_SUMMARY.yaml` 能解析，且 `operation: none` 条目的空字段、证据列表和审批标志符合合同。
- 工程事实生成器校验通过：9 个领域、48 条事实。

## 模块内容

- 范围、坐标/符号/单位、输入输出、地形生成、实测质控、有限球尖可达性、复合针体禁止碰撞、首次接触、方向候选、事件定位、验证和 A2/A3 交接均存在。
- A1 没有引入摩擦稳定、接触力、梁/弹簧平衡、材料失效或多刺载荷共享。
- Markdown 数学块、代码围栏和引用编号闭合。
- 接受前修正一处各向异性 PSD 旋转变量漏用，详见 `MECHANICAL_FIXES.md`。

## 引用核验

- 本地文献引用只使用“文献编号”形式。
- 12 项顺序引用均在正文使用且均有定义，无悬空或未用条目。
- 外部来源逐一检查为可访问的原始论文或官方页面；PSD 定义与带宽、NIST 测量带通、ISO/FEPA 粒度分级范围以及混凝土测量分辨率的表述均有对应来源支持。
- `CITATION_BRIEF.md` 仅保存在本轮运行目录，不进入 A2 默认上传链。

## 可复现校验

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 derivation/runs/A1/validate_artifacts.py
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
```

两条命令均已通过。
