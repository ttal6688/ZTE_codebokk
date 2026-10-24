# UPA单极化双流400位置完整扫描数据

2026年10月24日。每个配置使用冻结位置1至400，分别测试LOS与MIX。CPU为HAQSE、DFT、POS三种模型相位方法；UE为Type-I、Type-II、Docomo结构适配、HAQSE、DFT、POS六种观测相位方法。每种方法都保存配对的单流与双流，另有真实CSI直接SVD单流和等功率双流参考。

16组参数配置对应19个曲线标签，实际明细281,600条，展开334,400条；实际可实施单双流配对115,200组，展开136,800组。默认配置复用四次，不能按独立样本重复统计。完整报告在[Markdown](../../docs/UPA单极化双流400位置完整实验报告.md)与[Word](../../docs/UPA单极化双流400位置完整实验报告.docx)。

## 正文和补充实验

最新报告按CPU、UE分别组织。每端正文只列三项定位误差（SNR、天线数、AP数）、三项吞吐量（SNR、天线数、莱斯因子）及反馈比特数与AP数。AP数与吞吐量、单双流增量、第二模式、CDF和默认配置对照保留在末尾补充。

CPU性能与反馈图加入全反馈Type-I(UE)、全反馈Type-II(UE)、Docomo(UE)，复用原UE结果。定位误差图只含三种有位置输出的方法。

定位误差由原双流空间反馈比特串恢复，并与冻结位置计算欧氏距离，未重跑信道观测和相位设计。新增文件为dual_position_trials.csv.gz、dual_position_summary.csv、dual_position_source.json；CPU共享参考来源见CPU_UE_reference_summary.csv。

## 参数与文件对应

| case | UPA阵元数 | AP数 | 观测SNR dB | K dB | 曲线用途 |
|---|---:|---:|---:|---:|---|
| 01 | 1024 | 8 | 20 | 10 | SNR |
| 02 | 1024 | 8 | 25 | 10 | SNR |
| 03 | 1024 | 8 | 30 | 10 | 四条曲线共用默认配置 |
| 04 | 1024 | 8 | 35 | 10 | SNR |
| 05 | 1024 | 8 | 40 | 10 | SNR |
| 06 | 64 | 8 | 30 | 10 | UPA规模 |
| 07 | 256 | 8 | 30 | 10 | UPA规模 |
| 08 | 1024 | 5 | 30 | 10 | AP数 |
| 09 | 1024 | 6 | 30 | 10 | AP数 |
| 10 | 1024 | 7 | 30 | 10 | AP数 |
| 11 | 1024 | 9 | 30 | 10 | AP数 |
| 12 | 1024 | 10 | 30 | 10 | AP数 |
| 13 | 1024 | 8 | 30 | 0 | K |
| 14 | 1024 | 8 | 30 | 5 | K |
| 15 | 1024 | 8 | 30 | 15 | K |
| 16 | 1024 | 8 | 30 | 20 | K |

纯LOS不使用K，K扫描中LOS为一致性对照。数据SNR固定，SNR横轴仅为CSI观测质量。400 MHz直接由窄带频谱效率换算Mbps。

每组位于cases/case_XX，包含17,600条明细：800个位置与信道组合，每组合22行，其中CPU8行、UE14行。每组均有参数合同、运行审计、独立审计、汇总和单双流配对。

- dual_stream_trials.csv.gz：完整消息、比特串、系数、有效信道、发送签名、功率、每流SINR与模式等。
- single_dual_pairs.csv.gz：该配置8,800组配对，含SVD参考。
- dual_stream_summary.csv：该配置分端、分信道、分方法、分流数均值。
- 根目录single_dual_pairs.csv.gz与dual_stream_summary.csv：按19个标签展开的配对与汇总。
- method_feasibility_summary.csv：每种方法各曲线点的增量、最小增量、正收益率和第二模式统计。
- nonpositive_gain_cases.csv：所有非正收益，不删样本；含重复默认曲线标签。按case_id、端、信道、方法、位置去重可得到实际条目数。
- CPU与UE目录：各35幅PNG和对应可编辑FIG，纯LOS与MIX分开。
- independent_full_audit.json：覆盖、消息重放、独立指标、旧单流逐样本对齐及两项对照检查。
- compression_manifest.json：压缩与解压后SHA256、大小和无损校验。
- source_and_input_SHA256.json：运行代码与冻结输入版本，文本CRLF统一成LF后计算。

## 解压与复现

Python可以直接读gzip，必须将反馈串作为字符串读取，以保留前导零：

```python
import pandas as pd
t = pd.read_csv('cases/case_03/dual_stream_trials.csv.gz',
                dtype={'feedback_wire': 'string'})
```

MATLAB的gunzip可解压到新目录。统一绘图使用根目录汇总、配对和dual_position_summary.csv；首次恢复定位误差先运行python derive_dual_position_results.py results/dual_stream_full400。其余性能绘图只需汇总和配对，缺少配对CSV时会从gzip解压，不需要加载全部原始明细。Python两级审计均支持直接读取压缩文件。

```matlab
addpath('8.单流');
experimentDir=fullfile(pwd,'8.单流','results','new_dual400');
run_dual_stream_task2('OutputDir',experimentDir);
plot_precoding_results(experimentDir);
```

```text
python audit_dual_stream_full.py results/new_dual400 --stage cases
```

```matlab
verify_dual_stream_replay(experimentDir);
```

```text
python audit_dual_stream_full.py results/new_dual400 --stage summary
python package_dual_stream_results.py results/new_dual400
```

并行时在不同MATLAB进程指定Stage=run、Worker=1至4、Workers=4，写同一个新的experimentDir。四个进程结束后，单独运行Stage=finalize再绘图和审计。仅写互不重叠的配置目录，不需要并行工具箱。运行器拒绝覆盖已完成结果。

默认最小验证及历史单流结果未覆盖。本轮仅扩大仿真范围，第二流实现保持共享空间波束、固定第一相位、UE新增4(B−1) bit和CPU模型内生成第二相位。

连续CPU相位搜索的跨数值库分支差异超过1e−3系数阈值时，独立审计保留pending状态，导出CPU_continuous_replay_required.csv。verify_dual_stream_replay仅用原平台的公共几何与消息重放这些记录，系数及发送签名误差须低于1e−10；最终汇总审计同时检查该重放凭据。真实信道和速率仍全部由Python独立核验。未因跨实现分支差异调高系数阈值或修改原算法。
