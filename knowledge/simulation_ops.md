# 仿真操作指南 — MATLAB/Simulink

## 基本操作流程

### 打开并运行模型

**Step 1：启动MATLAB**
- 打开MATLAB R2020b及以上版本（需含Simscape Electrical工具箱）
- 确认已安装：Simulink、Simscape、Simscape Electrical、DSP System Toolbox

**Step 2：打开模型文件**
```matlab
% 方法1：在MATLAB命令窗口输入
open_system('MMCSIDUAN0x11')

% 方法2：在文件浏览器中双击 MMCSIDUAN0x11.slx
```

**Step 3：检查求解器设置**
- 菜单 → 仿真 → 模型配置参数（Ctrl+E）
- 求解器类型：固定步长（Fixed-step）
- 求解器：Discrete (no continuous states)
- 固定步长：0.0001（100μs）
- 停止时间：20

**Step 4：运行仿真**
- 点击工具栏"运行"按钮（▶），或按Ctrl+T
- 等待仿真完成（20s仿真，实际耗时取决于子模块数和电脑性能）
- 大约需要5-30分钟（子模块数越多越慢）

**Step 5：查看结果**
- 双击Scope模块查看波形
- 或在命令窗口读取工作空间变量

### 修改仿真参数

**修改仿真时间**：
- 工具栏右上角直接修改"停止时间"
- 调试时建议先设为2-5s，确认无误后再跑20s

**修改求解器步长**：
```matlab
% 命令行方式修改
set_param('MMCSIDUAN0x11', 'FixedStep', '5e-5')  % 改为50μs
```

## 添加直流电压源替代光伏

### 导师任务理解

导师要求：用直流电压源先代替光伏基地，看仿真结果。

这意味着在直流侧接入一个恒定的直流电压源，模拟光伏阵列的稳态输出。

### 操作步骤

**Step 1：确定接入位置**
- 直流电压源应接在MMC换流站的直流侧
- 具体位置：MMC2（定有功功率站）的直流母线正负极之间
- 或者在两个MMC之间的直流线路上引出分支接入

**Step 2：添加直流电压源模块**
1. 在Simulink库浏览器中找到：
   - Simscape → Electrical → Specialized Power Systems → Sources
   - 选择 "DC Voltage Source"
2. 拖入模型的直流母线位置
3. 用导线将正负极连接到直流母线

**Step 3：设置电压源参数**
- 双击DC Voltage Source模块
- 设置电压值 = 光伏阵列等效输出电压
  - 如果系统直流电压为±150kV，则电压源设为300kV（正负极间）
  - 如果系统直流电压为±20kV，则设为40kV
  - 如果系统直流电压为±10kV，则设为20kV
- 内阻可设为0.01Ω（近似理想电压源）

**Step 4：添加串联电阻（可选）**
- 为避免理想电压源与MMC直流电容直接并联导致数值问题
- 在电压源和母线之间串联一个小电阻（0.01-1Ω）
- 库位置：Simscape → Electrical → Passive → Series RLC Branch

**Step 5：调整控制策略**
- 接入电压源后，MMC1（定Udc站）的控制目标需与电压源协调
- 方案一：电压源电压 = MMC1的Udc参考值 → 两者协同维持电压
- 方案二：电压源电压略高于Udc_ref → 电压源向系统注入功率（模拟光伏发电）

### 替代方案：受控电压源

如果需要模拟光伏出力变化，可使用受控电压源：
1. 使用 "Controlled Voltage Source" 模块
2. 输入端接一个Step/Ramp信号源模拟光照变化
3. 或接一个Lookup Table模拟日内出力曲线

```matlab
% 在MATLAB工作空间定义光伏出力曲线
t_pv = [0 2 5 10 15 20];        % 时间点(s)
v_pv = [0 300 300 280 260 300]; % 对应电压(kV)
% 在Simulink中用 From Workspace 模块读取
```

## 参数调节指南

### PI控制器调参

**内环PI（电流环）**：
- 带宽要求：1-5kHz（响应快）
- 典型参数：Kp = 0.5-2.0, Ki = 50-200
- 调参方法：
  1. 先设Ki=0，调Kp使阶跃响应无稳态误差
  2. 逐步增大Ki消除稳态误差
  3. 观察是否振荡，振荡则减小Kp

**外环PI（电压/功率环）**：
- 带宽要求：10-100Hz（比内环慢5-10倍）
- 定Udc外环典型参数：Kp = 5-20, Ki = 100-500
- 定P外环典型参数：Kp = 0.5-2, Ki = 20-100
- 调参原则：外环带宽 ≤ 内环带宽的1/5

### 子模块参数调节

**子模块数N**：
- N越大 → 输出波形质量越好（阶梯数越多），THD越低
- N越大 → 仿真速度越慢，内存需求越大
- 建议值：
  - 研究用（快速仿真）：N = 10-20
  - 工程级仿真：N = 36-72
  - 实际工程：N = 200-400

**子模块电容Csm**：
- Csm越大 → 电容电压纹波越小，系统越稳定
- Csm越大 → 子模块体积成本越大
- 典型范围：2-15 mF
- 计算依据：

$$C_{sm} = \frac{2 S_{rated}}{N \cdot \omega \cdot U_{c0}^2 \cdot \epsilon}$$

其中 $\epsilon$ 是允许的电压纹波比（通常5-10%）

**桥臂电感Larm**：
- Larm越大 → 环流抑制效果越好，故障电流上升率越低
- Larm越大 → 系统动态响应越慢
- 典型范围：Larm = 0.05-0.15 p.u.
- 计算：$L_{arm} = k \cdot \frac{U_{dc}}{2 \omega I_{rated}}$，k通常取0.1-0.15

## 常见问题排查

### 仿真不收敛

**现象**：运行后MATLAB报"Simulation is not converging"或仿真中断

**排查步骤**：
1. 检查步长是否太大 → 减小到50μs或20μs
2. 检查是否存在代数环 → 在代数环中加单位延迟（Unit Delay）
3. 检查初始条件 → 确保所有积分器有合理初始值
4. 检查电容初始电压 → 子模块电容初值设为 Udc/N

### 启动暂态过大

**现象**：仿真前1-2s出现极大的电压/电流尖峰

**解决方案**：
1. **预充电策略**：
   - 先闭锁换流器（所有PWM为0）
   - 通过交流侧不控整流给电容充电
   - 电容电压达额定值的85-90%后解锁换流器
   - 在Simulink中实现：Step信号控制使能端，延时0.5-1s

2. **斜坡启动**：参考值从0逐渐升至目标值
```matlab
% 在Simulink中添加Rate Limiter
% Udc_ref: 从0到300kV，斜率60kV/s → 5s达到额定
```

3. **降低初始功率参考**：P_ref从0逐步增加

### 波形持续振荡

**现象**：P/Q或Udc波形稳态后仍有持续振荡

**可能原因与解决**：
| 振荡频率 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 2×50Hz=100Hz | 桥臂环流 | 启用环流抑制控制器（CCSC） |
| 50Hz | 内环PI参数不当 | 减小Kp或增大阻尼 |
| 10-30Hz | 外环与内环耦合 | 降低外环带宽 |
| 5-10Hz | PLL与控制器交互 | 降低PLL带宽 |
| <5Hz | 系统功率振荡 | 增大直流电容或调整下垂系数 |

### Scope波形无法显示

**解决方法**：
1. 确认Scope连线正确
2. 检查数据类型是否为double
3. 右键Scope → 参数 → 设置合适的时间范围和幅值范围
4. 确认仿真已运行完成

## 导出仿真数据

### 导出到MATLAB工作空间

在模型中使用 "To Workspace" 模块：
1. 从信号线引出分支
2. 连接 To Workspace 模块
3. 设置变量名（如 Pout, Qout, Udc）
4. 格式选择 "Array" 或 "Timeseries"

### 导出为MAT文件

```matlab
% 仿真运行后
save('simulation_results.mat', 'Pout', 'Qout', 'Udc', 'tout')
```

### 绘制高质量图表

```matlab
figure;
plot(tout, Pout/1e6, 'b-', 'LineWidth', 1.5);
hold on;
plot(tout, Qout/1e6, 'r--', 'LineWidth', 1.5);
xlabel('时间 (s)', 'FontSize', 12);
ylabel('功率 (MW/MVar)', 'FontSize', 12);
legend('有功功率P', '无功功率Q', 'FontSize', 11);
title('MMC换流站功率响应', 'FontSize', 14);
grid on;
set(gca, 'FontName', 'SimHei');  % 中文字体
saveas(gcf, 'P_Q_response.png');
```
