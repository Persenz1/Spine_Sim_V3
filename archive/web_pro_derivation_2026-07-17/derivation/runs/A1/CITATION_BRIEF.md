# A1 简短引用说明

> 运行：`A1`  
> 提示词版本：`1.2.0`  
> 用途：仅本地归档；不进入后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

采用以下二维 PSD 约定：

$$
C_h(\mathbf q)=\int R_h(\mathbf r)e^{-i\mathbf q\cdot\mathbf r}\,d^2\mathbf r,
\qquad
\langle h^2\rangle=\frac{1}{(2\pi)^2}\int C_h(\mathbf q)\,d^2\mathbf q.
$$

有限周期域上的随机场通过 Hermitian 对称 Fourier 系数生成；离散振幅必须与所选 FFT 归一化一致，且生成后回算完整二维 PSD、方向谱和谱矩验证 [1,2,3]。

对单值高度场 $\Omega_h=\{z\le h(x,y)\}$，完整球尖的最低球心包络为

$$
H_R(x_c,y_c)=
\sup_{(u-x_c)^2+(v-y_c)^2\le R^2}
\left[
 h(u,v)+
 \sqrt{R^2-(u-x_c)^2-(v-y_c)^2}
\right],
$$

$$
g_R^{(z)}=z_c-H_R.
$$

$g_R^{(z)}$ 是高度场竖向包络残差；跨高度场/网格比较和保守推进使用欧氏有符号间隙 $g_R^{(d)}=\phi_\Omega(\mathbf c)-R$。该配置空间/Minkowski 包络删除有限球尖不可达的细小凹部；支持点由最大值集合恢复，多点支持不得平均成单一伪法向。实际针尖是局部球冠，故完整球包络之后还必须做球冠合法性及锥段、针杆、安装座碰撞检查 [4,5,3]。

对指向自由空间的接触法向 $\mathbf n$ 和局部 $+x$ 拖拽单位方向 $\mathbf d$，A1 的方向几何裕度定义为

$$
\eta_x=-\mathbf n\cdot\mathbf d.
$$

$\eta_x>0$ 只表示法向具有抵抗拖拽的分量，是 A2 摩擦/平衡前的必要几何筛选；它不是稳定挂接或承载判据 [4,5,3]。

非承载部件 $K_k$ 的净安全间隙统一写为

$$
g_k(\mathbf q)=
\min_{\mathbf x\in K_k(\mathbf q)}\phi_{\Omega}(\mathbf x)
-\delta_{\mathrm{clr},k},
$$

其中 $\phi_{\Omega}$ 为墙体实体有符号距离。首次接触和碰撞事件采用保守推进、回退括区及二分/Brent 类根定位，不能只检查固定步长两端，也不能改变真实拖拽速度替代数值减步 [3]。

## 2. 关键方法选择与结论来源

- 首版合成主线选择有限波数窗二维方向 PSD；实测数据可用且通过尺度质控时优先使用实测表面。各向同性径向 PSD 只能作为摘要，不能替代方向谱 [1,2]。
- PSD 只约束二阶统计。高度偏度/峰度可用二维 IAAFT 显式分支，孔洞、凸粒和条纹使用经材料测量标定的标记特征过程；所有非高斯处理后均须重新回算 PSD 和球尖可达性 [3]。
- 红砖表面必须保留位置、方向、统一基准面和局部分区信息；单条二维轮廓、单一 $R_a$ 或文献中的二维/三维均值比例不足以生成代表性三维地形 [6]。
- 仪器物理分辨率、采样间距、数值网格间距和可信波长范围必须分别记录；有限测区、去趋势、仪器传递和噪声会改变所得 RMS、相关尺度及短波导数量 [6,7,8]。
- FEPA P 目数描述磨粒粒度分布/分级体系，不唯一决定成品砂纸的三维峰高、突出量、面密度、粘结层或 PSD；这些量需对具体批次测量 [9,10,11]。
- 混凝土表面统计必须绑定具体表面处理和测量尺度；外部数据仅支持“处理与分辨率会改变参数”的边界，不作为本项目唯一数值 [12]。
- 工程事实直接适用：`SURFACE.HEIGHT_FIELD.PRIMARY`、`SURFACE.TRIANGLE_MESH.SECONDARY`、`NEEDLE.TIP.GEOMETRY`、`NEEDLE.CONTACT.COLLISION_BOUNDARY`、`NUMERICS.DRAG.VARIABLE_STEP`。这些事实不分配顺序参考文献号。
- 文献 01 的摩擦稳定公式属于 A2；文献 11 的弹性半空间接触理论不是 A1 针尖承载模型；文献 12 的二维/三维比例不是换算常数；文献 16 的候选三角形数量不是成功概率或承载力 [1,4,5,6]。

## 参考来源

[1] 文献11

[2] https://arxiv.org/pdf/1607.03040

[3] GPT 自带知识：二维随机场 Hermitian 谱合成与离散 PSD 回算、二维 IAAFT、Minkowski/形态学球尖包络、有符号距离、BVH/AABB 最近距离、刚体保守推进和括区根定位；适用于刚性几何和通用数值方法，材料统计、仪器带宽和工程容差仍需测量或审批。

[4] 文献01

[5] 文献16

[6] 文献12

[7] https://www.nist.gov/publications/robust-evaluation-statistical-surface-topography-parameters-using-focus-variation

[8] https://www.iso.org/standard/74591.html

[9] https://fepa-abrasives.org/abrasives/standards/

[10] https://www.iso.org/standard/78220.html

[11] https://www.iso.org/standard/78219.html

[12] https://www.mdpi.com/1996-1944/18/23/5320
