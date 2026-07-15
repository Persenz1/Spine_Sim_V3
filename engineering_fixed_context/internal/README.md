# 工程固定上下文事实库

本目录是上一级 `engineering_fixed_context.md` 的结构化后台。日常人工审阅以上一级完整 Markdown 为准；YAML 用于一致性校验、版本管理，以及未来生成程序配置、参数表和网页表单。

## 单一维护方向

```text
facts/*.yaml -> build_context.py -> ../engineering_fixed_context.md
```

不要同时手工修改 YAML 和生成后的 Markdown。工程事实经人工确认后写入 YAML，再重新生成 Markdown。

## 内容边界

本库可以记录：

- 坐标、方向、编号和单位；
- 几何尺寸、参数范围和扫描集合；
- 运动自由度、边界条件和加载工况；
- 模型开关、接口能力、输出要求；
- 首版排除项和尚未固定的参数。

本库不记录：

- 接触互补方程或摩擦稳定域的具体实现；
- 梁柔顺、活动集、损伤演化和载荷重分配算法；
- 单刺、阵列或整爪状态机；
- A/B/C 模块的推导过程。

这些机理内容应进入 `RESULT`、`MODULE_CONTEXT` 和模块间合同。

## 状态含义

- `fixed`：定义或唯一值已固定；
- `fixed_set`：扫描集合已固定；
- `fixed_range`：允许范围已固定，具体离散点可以尚未固定；
- `model_switch`：是否启用某能力由固定开关控制；
- `interface_required`：实现未固定，但程序接口必须具备该能力；
- `unresolved`：程序需要考虑，但当前禁止硬编码为唯一值；
- `excluded`：首版明确不处理。

## 生成与校验

在仓库根目录运行：

```powershell
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --check
conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --write
```

`--check` 校验 YAML 结构、事实 ID、状态、作用域和生成结果是否与根目录 Markdown 一致；`--write` 重新生成完整 Markdown。
