# 单流任务二运行与实验口径

本说明对应 [run_single_stream_task2.m](run_single_stream_task2.m)，不对应历史双极化程序。当前实现为单极化单流ULA；UPA尚待适配。CPU和UE分别见 [CPU说明](docs/CPU说明.md)、[UE说明](docs/UE说明.md)，已有结果见 [数据索引](results/single_stream_full/README.md)。

## 运行

MATLAB进入本文件所在目录，先在新目录做流程检查，避免覆盖归档结果：

```matlab
run_single_stream_task2('Mode','smoke','OutputDir',fullfile(pwd,'results','single_stream_smoke_review'));
run_single_stream_task2('Mode','full','OutputDir',fullfile(pwd,'results','single_stream_full_review'));
```

默认smoke使用前6个位置，full使用前400个位置；两者位置重叠，smoke是流程检查，不是独立样本验证。可用Samples指定位置数，MakeFigures控制出图。旧双极化verify/run入口不用于当前单流程序。

## 公共模型与扫描

| 项目 | 当前实际设置 |
|---|---|
| 阵列与端口 | ULA 每AP 16/32/64个单极化阵元 UE有4个接收空间位置 |
| 信道与流数 | 单AP信道4×N 联合信道4×BN 只发送一条流 |
| 波束与功率 | 每AP一个空间波束及一个单位模相位 总功率1 每AP功率1/B；理想SVD放松每AP等功率约束 |
| 带宽 | 400 MHz 仅用于窄带速率换算 未实现400 MHz频率选择性或OFDM |
| 参考AP | HAQSE和DFT使用R=3 位置方法从相同参考方向定位后发送二维坐标 |
| 位置与散射 | 沿用第6目录冻结位置、噪声种子和六散射体输入 |
| SNR扫描 | 20、25、30、35、40 dB 其他参数N=64 B=8 K=10 dB |
| 阵元数扫描 | 16、32、64 其他参数B=8 观测SNR=30 dB K=10 dB |
| AP数扫描 | 5至10 其他参数N=64 观测SNR=30 dB K=10 dB |
| 莱斯因子扫描 | 0、5、10、15、20 dB 其他参数N=64 B=8 观测SNR=30 dB |

四类扫描合计19个设置标签，默认工作点在不同扫描中重复出现，不能理解成19种互不重叠的物理配置。横轴SNR为信道观测SNR，不是随横轴改变的数据链路SNR；数据链路沿用冻结配置的rho_data。

## 方法与反馈

令M=8N，d=log2(M)。当前一般AP间相位量化为4 bit，而不是旧说明所写的QPSK；Docomo内部beta为2 bit QPSK。

| 方法 | CPU图中的信息来源 | UE图中的信息来源 | 每次更新有效载荷 |
|---|---|---|---|
| HAQSE R3 | 量化频率定位后重构共相位 | 同一空间消息加观测CSI共相位 | CPU 42 bit UE 42+4(B−1) bit |
| DFT-index R3 | 方向索引定位后重构共相位 | 同一空间消息加观测CSI共相位 | CPU 3d bit UE 3d+4(B−1) bit |
| POS R3 | 24 bit二维坐标重构共相位 | 同一坐标加观测CSI共相位 | CPU 24 bit UE 24+4(B−1) bit |
| Type-I | 共享UE-CSI基线 | 每AP一个空间波束加AP间相位 | Bd+4(B−1) bit |
| Type-II | 共享UE-CSI基线 | 每AP双波束复合加AP间相位 | 2Bd+5B+4(B−1) bit |
| Docomo适配 | 不列入CPU链路 | 本地4倍DFT QPSK beta AP逻辑栅格DFT交替更新 | B ceil(log2(4N))+2(B−1)+ceil(log2(B)) bit |
| 理想SVD | 真实完整信道参考 | 同一参考 | 不设有限反馈预算 CSV为NaN |

CPU图中出现Type-I/II和SVD只是共享参考，不能说它们也仅由三个参考AP的几何消息实现。“全反馈”是仓库方法标签，Type-I/II实际反馈码本索引及系数，不传完整CSI矩阵。

R=3描述参考消息来源数量，不是CPU重构矩阵维度。CPU实际为B个AP构造4×BN模型并求主模式；UE共相位同样依赖全部参与AP的观测信道。CSV旧字段cpu_estimation_dimension取值3或2，应按 [整理说明](docs/整理说明.md) 解读。

坐标仍为24 bit，但当前代码按估计位置和活动AP计算x/y分配，不是第6目录冻结的12/12规则；分配信息如何由CPU获得尚未在独立消息解码流程中验证，报告不据此声称协议已闭环。

## 输出

逐样本文件single_stream_trials.csv、分组均值single_stream_summary.csv和实验配置experiment_contract.json写入指定结果目录；CPU/与UE/分别保存图。脚本带有发射功率和真实信道主模式功率参考检查，已有audit.json的complete表示原程序执行完成，不等于经过完整独立消息审计。
