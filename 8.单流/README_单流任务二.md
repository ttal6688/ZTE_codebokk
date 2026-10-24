# UPA单流运行与实验口径

当前最终口径及本轮推进安排见[实验口径与推进顺序](docs/当前实验口径与推进顺序.md)。主参考为真实信道直接SVD；同算法CSI配对仅为补充诊断。

当前反馈整数协议SSTR_V2，正式运行版本UPA_SINGLE_PROTOCOL_V3，所有可实施预编码均由实际打包的整数比特串恢复。方法名、模式、活动AP顺序、码本和量化配置是双方预先共享的配置；统计反馈有效载荷，不含传输头、FEC、字节填充。JSON只是便于检查，JSON文本长度不是反馈bit数。

## 运行

在MATLAB中进入本目录：

```matlab
verify_single_stream_protocol('results/my_V2_verify');
run_single_stream_task2('Mode','verify','OutputDir','results/my_V2_verify','MakeFigures',false);
run_single_stream_task2('Mode','smoke','OutputDir','results/my_V2_smoke','MakeFigures',true);
```

`verify`默认位置399、400，四组UPA/AP设置，每组分别测试LOS和MIX；`smoke`默认位置1至4，12个参数标签，默认MIX。可使用`Samples`指定从1开始的样本数，使用`ChannelModels`, `{'LOS','MIX'}`指定模型。已有CSV的输出目录会被拒绝，以保护历史数据。`verify_single_stream_protocol`只写检查JSON，可先写入同一空结果目录。

完整400位置扫描已完成，默认关闭补充CSI配对；复现请使用新目录：

```matlab
run_single_stream_task2('Mode','full','IncludeCSIPairs',false,'OutputDir','results/my_full400');
```

完整结果见[正式单流报告](docs/UPA单流400位置正式实验报告.md)。同算法CSI配对由IncludeCSIPairs控制：验证/流程模式默认开启，full模式默认关闭。

完整扫描为观测SNR20:5:40 dB、每AP阵元数64/256/1024、AP数5:10、莱斯因子0:5:20 dB，共19个参数标签。默认32×32、B=8、观测SNR30 dB、K=10 dB；各扫描的默认点会重复，用于各自画图，不当作额外独立样本。

独立Python审计（依赖numpy、pandas）：

```text
python audit_single_stream_protocol.py results/my_V2_verify results/my_V2_smoke
```

旧`audit_single_stream_upa.py`只用于V1历史修复数据，不要用它替代V2完整协议审计。

## 整数有效载荷格式

所有整数MSB优先，矩阵按MATLAB列顺序编码。令d为二维码字索引bit数，即d=2log2(4sqrt(N))。所有UE普通方案固定首AP相位为0，其余AP相位4 bit；先去除共同相位，再量化。

| 方法 | 字段顺序 | CPU几何方案 | UE方案 |
|---|---|---:|---:|
| HAQSE | 3个AP的二维频率整数，每维14 bit；随后UE相位 | 84 | 84+4(B−1) |
| DFT | 3个AP的二维方向整数，每维log2(4sqrt(N)) bit；随后UE相位 | 3d | 3d+4(B−1) |
| POS | x/y/z整数，13/14/9 bit；随后UE相位 | 36 | 36+4(B−1) |
| Type-I | 每AP一个二维码字的线性索引；随后相位 | 仅作UE参考 | Bd+4(B−1) |
| Type-II | 每AP两个线性索引；每AP3 bit幅度、2 bit内部相位；随后AP相位 | 仅作UE参考 | 2Bd+5B+4(B−1) |
| Docomo结构适配 | 每AP一个线性索引；B−1个2 bit beta；一个AP逻辑DFT索引 | 不参加CPU几何链路 | Bd+2(B−1)+ceil(log2(B)) |

Type-II使用直接索引编码，没有利用正交组关系压缩索引；表中是当前实际有效载荷。默认N=1024、B=8时，CPU几何HAQSE/DFT/POS为84/42/36 bit；UE为112/70/64 bit；Type-I/II为140/292 bit；Docomo结构适配为129 bit。

## 输出解释

开启补充CSI配对时，每个案例保存CPU六行：SVD、两个UE基线参考、三个CPU几何方法；UE十三行：SVD、六个观测CSI方法、六个同算法完美CSI方法。`role`明确区分CPU_METHOD、UE_REFERENCE、UE_METHOD、UPPER_BOUND。关闭配对时总共13行，UE只有SVD与六种观测CSI方法。主图只使用观测CSI和SVD；补充完美CSI单独通过`paired_CSI.csv`比较。

CSV保存完整消息、比特串、AP系数、预编码检查量、量化前/解码后坐标及越界标志，并记录接收功率、频谱效率、400 MHz换算速率。`cpu_estimation_dimension`已移除，改为分项信息量、模型尺寸和计时。

`reference_observation_complex_count`是UE生成参考AP几何消息所需的原始观测规模，不是CPU获得的信道；对UE方案它是全部AP观测的子集，不与`full_observation_complex_count`相加。模型尺寸只记录CPU实际构造的4×BN模型。`decoder_time_s`只计CPU解码接口；UE的`shared_frontend_time_s`是同一算法族共享的前端时间，重复列出，不代表每种算法独立运行复杂度，也不用于性能排名。

400 MHz仅作窄带SE换算；观测SNR控制CSI噪声，数据链路rho另由公共参考功率和10 dB参考SNR确定。理想SVD放松每AP等功率限制。完美CSI配对不保证每个样本速率上升，因为当前投影、码本和量化规则并非速率全局最优。


## 单极化双流最小验证

```matlab
verify_dual_stream('results/my_dual_unit');
run_dual_stream_minimal('OutputDir','results/my_dual32');
plot_precoding_results('results/my_dual32');
```

默认32个预定位置、LOS与MIX、32×32/B=8/观测30 dB。共享原单流空间消息和第一相位，UE再追加28 bit第二相位；CPU由模型独立计算、不增加bit。双流矩阵C为B×2，两流每AP合计功率1/B。Docomo保留其单流结构，额外相位属于统一双流扩展，非论文原始多列DFT子集复现。

```text
python audit_dual_stream.py results/dual_stream_minimal32
```

当前完整CSV在本地保留，GitHub的单流明细为csv.gz。Python审计自动读取压缩文件；MATLAB统一绘图入口可先解压。检查点不作为新增独立数据发布。

## 单极化双流完整扫描

run_dual_stream_task2复用上述单配置实现，400位置、LOS与MIX、观测SNR20至40 dB、UPA 64/256/1024阵元、AP 5至10、K 0至20 dB。16组参数配置对应19个曲线标签，完整明细按配置分组无损压缩，CPU与UE分开出图。

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

结果与复现细节见[完整双流报告](docs/UPA单极化双流400位置完整实验报告.md)和[数据说明](results/dual_stream_full400/README.md)。第二流算法与最小验证一致，非正收益逐条保存；每个MIX单流基线与上一轮400位置单流按位置和配置核对。


## 最新报告的实验正文

单双流均按CPU和UE分开，分别列定位误差与SNR、天线数、AP数，吞吐量与SNR、天线数、莱斯因子，以及反馈比特数与AP数。其他已做实验保留在末尾补充。CPU双流Type-I、Type-II、Docomo均作为UE共享参考展示，不改为CPU几何算法。

双流定位误差未在原性能汇总中单列，可直接从保存的空间反馈比特串恢复，不重跑信道和相位搜索：

```text
python derive_dual_position_results.py results/dual_stream_full400
```

随后使用原统一绘图入口。DFT索引和位置反馈图例不再显示R=3，实际定位参考AP数量仍为3。
