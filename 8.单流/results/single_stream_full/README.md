# 既有单流结果归档索引

这些文件来自single_stream原分支的既有运行。本目录实际对应单极化单流ULA，按400 MHz换算吞吐量；不是UPA或双极化实验。本次整理不重算曲线，也不替换原数据。

## 数据范围

| 项目 | 原归档内容 |
|---|---|
| 位置数 | 每个设置400个位置 |
| 设置标签 | SNR 5个 阵元数3个 AP数6个 莱斯因子5个 合计19个 |
| CPU记录 | 45,600条 含6种方法 |
| UE记录 | 53,200条 含7种方法 |
| 总记录 | 98,800条 |
| 分组均值 | 247行 每组400位置 |
| 理想参考 | 相同真实信道SVD 在CPU/UE图中重复列出 |

不同扫描中默认工作点重复；CPU/UE中的共享基线也重复列出。98,800是存储行数，不是独立信道或独立位置数量。

## 文件

- [single_stream_trials.csv](single_stream_trials.csv)：逐样本数据。
- [single_stream_summary.csv](single_stream_summary.csv)：分组均值。
- [experiment_contract.json](experiment_contract.json)：原执行配置。其中固定维度CPU_note已由新说明纠正，原文件保留作为执行时记录。
- [audit.json](audit.json)：原程序运行完成标记；完整消息编解码核查尚待补齐。
- [本次数据与目录核查](../../organization_audit.json)：原始文件保留及分组核查。

## CPU与UE分别阅读

CPU方法和信息边界见 [CPU说明](../../docs/CPU说明.md)；UE方法和反馈开销见 [UE说明](../../docs/UE说明.md)。

| 图类别 | CPU图 | UE图 |
|---|---|---|
| 定位误差与观测SNR | [CPU](CPU/CPU_定位误差_SNR.png) | [UE](UE/UE_定位误差_SNR.png) |
| 定位误差与阵元数 | [CPU](CPU/CPU_定位误差_天线数.png) | [UE](UE/UE_定位误差_天线数.png) |
| 定位误差与AP数 | [CPU](CPU/CPU_定位误差_AP数.png) | [UE](UE/UE_定位误差_AP数.png) |
| 吞吐量与观测SNR | [CPU](CPU/CPU_吞吐量_SNR.png) | [UE](UE/UE_吞吐量_SNR.png) |
| 吞吐量与阵元数 | [CPU](CPU/CPU_吞吐量_天线数.png) | [UE](UE/UE_吞吐量_天线数.png) |
| 吞吐量与莱斯因子 | [CPU](CPU/CPU_吞吐量_莱斯因子.png) | [UE](UE/UE_吞吐量_莱斯因子.png) |
| 反馈bit与AP数 | [CPU](CPU/CPU_比特数_AP数.png) | [UE](UE/UE_比特数_AP数.png) |

同名FIG一并保留。定位图只有能产生位置估计的HAQSE、DFT和POS；Type-I/II与Docomo没有相应定位曲线。

速率不扣除反馈/导频占用。一般AP间相位实际为4 bit，不是QPSK；历史cpu_estimation_dimension字段也不是CPU矩阵维度，详见 [整理说明](../../docs/整理说明.md)。
