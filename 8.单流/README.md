# UPA单极化单流与双流实验

## 2026年10月25日 低至高观测SNR预实验

新增32位置单流范围诊断：CSI观测SNR为−20、−10、0、10、20、30、40 dB，数据链路参考SNR仍为10 dB。LOS与MIX、CPU与UE分别给出定位误差和吞吐量，另有同算法无观测噪声对照，共10幅图。主扫描8512条，对照704条；这是预实验，原400位置单双流正式报告保持不变。

[预实验MD报告 最新版](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.%E5%8D%95%E6%B5%81/docs/UPA%E5%8D%95%E6%B5%81%E4%BD%8E%E8%87%B3%E9%AB%98%E8%A7%82%E6%B5%8BSNR%E9%A2%84%E5%AE%9E%E9%AA%8C%E6%8A%A5%E5%91%8A.md) · [预实验Word报告](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.%E5%8D%95%E6%B5%81/docs/UPA%E5%8D%95%E6%B5%81%E4%BD%8E%E8%87%B3%E9%AB%98%E8%A7%82%E6%B5%8BSNR%E9%A2%84%E5%AE%9E%E9%AA%8C%E6%8A%A5%E5%91%8A.docx) · [数据及复现入口](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.%E5%8D%95%E6%B5%81/results/single_stream_snr_pilot32_20261025/README.md)

已看到低SNR退化与高SNR平台。以MIX位置反馈为例，−20至40 dB平均定位误差由约2.897 m降到0.01010 m，CPU吞吐量由2078.64升到3190.33 Mbps。纯LOS的无噪声连续定位约0.443 mm、坐标解码后约4.178 mm；MIX的连续定位无噪声残差约8.981 mm。UE吞吐量比CPU更早进入平台。不能据此要求全部曲线逐点单调。

已完成Docomo结构核对及专项验证、400位置单流正式扫描、400位置单极化双流完整扫描。双流覆盖LOS与MIX以及四类参数，CPU与UE分别说明和出图，主参考是完美CSI直接SVD；普通方法使用带噪观测，400 MHz直接换算。

最新单流与双流统一在Git分支feat/upa-single-dual-complete-20261024维护，后续修改继续使用该分支，见[维护约定](docs/当前维护分支.md)。两份报告逐实验附齐全部22幅单流图与70幅双流图、对应数值及解释；Word与Markdown内容一致。

图例统一为全反馈Type-I(UE)、全反馈Type-II(UE)、空间频率和Docomo；CPU对比同步包含Docomo(UE)共享参考，定位误差图不加入无位置输出的方法。名称与参考数据来源见[图例及CPU共享参考说明](docs/图例命名和CPU共享参考.md)，原始仿真数值不变。

## 报告正文安排

CPU与UE分别按同一大纲组织：定位误差与SNR、天线数、AP数；吞吐量与SNR、天线数、莱斯因子；反馈比特数与AP数。其他已做实验移到报告末尾额外补充，保留图片、数值和结论。双流定位误差由已保存的空间反馈消息恢复，定位前端与单流共用。

最新图例为全反馈Type-I(UE)、全反馈Type-II(UE)、空间频率、DFT索引、位置反馈和Docomo；CPU比较同步展示三种UE共享参考。参考AP数仍固定为3，只从图例删除R=3后缀。

## 最近更新与当前图形设置

最新单流和双流的AP数量横轴只显示整数 **5、6、7、8、9**，显示范围为 **5–9**。PNG、可编辑FIG和两份Word内嵌图片已同步；其他正文和排版保持不变，未追加Word检查。

该范围仅用于图形展示。原始扫描仍含5至10 AP，仿真结果和报告数值表中的10 AP数据没有删除或重新计算。最新报告链接见下方。

后续每次修改均须同步更新仓库首页及本README，包括仅修改图例、坐标轴或Word图片的情况；规则见[仓库维护规则](../AGENTS.md#每次修改必须同步维护readme)。

## 最新400位置报告

| 内容 | Markdown | Word |
|---|---|---|
| 单流正式结果及CPU与UE解释 | [单流完整报告 最新版](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.%E5%8D%95%E6%B5%81/docs/UPA%E5%8D%95%E6%B5%81400%E4%BD%8D%E7%BD%AE%E6%AD%A3%E5%BC%8F%E5%AE%9E%E9%AA%8C%E6%8A%A5%E5%91%8A.md) | [转发版](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.%E5%8D%95%E6%B5%81/docs/UPA%E5%8D%95%E6%B5%81400%E4%BD%8D%E7%BD%AE%E6%AD%A3%E5%BC%8F%E5%AE%9E%E9%AA%8C%E6%8A%A5%E5%91%8A.docx) |
| 双流400位置完整扫描及不利样本 | [双流完整报告 最新版](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.%E5%8D%95%E6%B5%81/docs/UPA%E5%8D%95%E6%9E%81%E5%8C%96%E5%8F%8C%E6%B5%81400%E4%BD%8D%E7%BD%AE%E5%AE%8C%E6%95%B4%E5%AE%9E%E9%AA%8C%E6%8A%A5%E5%91%8A.md) | [转发版](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.%E5%8D%95%E6%B5%81/docs/UPA%E5%8D%95%E6%9E%81%E5%8C%96%E5%8F%8C%E6%B5%81400%E4%BD%8D%E7%BD%AE%E5%AE%8C%E6%95%B4%E5%AE%9E%E9%AA%8C%E6%8A%A5%E5%91%8A.docx) |

以上两份为当前完整实验报告，已同步最新图例和CPU图中的Docomo(UE)。[返回仓库首页的最新报告入口](../README.md#最新报告入口)。

## 方法说明与前期验证

| 内容 | Markdown | Word |
|---|---|---|
| 如何从单流扩展双流及32位置前期最小结果 | [双流扩展说明与前期验证](docs/UPA单极化双流扩展验证报告.md) | [前期验证转发版](docs/UPA单极化双流扩展验证报告.docx) |
| Docomo论文对应与检查 | [专项说明](docs/Docomo结构适配与专项验证.md) | 包含于单流Word报告 |
| 最终信息与反馈口径 | [口径和推进顺序](docs/当前实验口径与推进顺序.md) | 包含于两份Word报告 |

## 数据与复现

- [单流400位置](results/single_stream_V3_full400/README.md)：98,800条记录，19个曲线标签，16个物理配置；原始明细为无损gzip，CPU与UE各11组图。
- [双流32位置](results/dual_stream_minimal32/README.md)：LOS和混合信道，1,408条记录，576个可实施方法配对，CPU与UE各7组图。
- [双流400位置](results/dual_stream_full400/README.md)：LOS和MIX，16个参数配置、19个曲线标签；CPU与UE各35组图，实际明细281,600条，展开334,400条。全部样本保留，非正收益单独列出。
- [Docomo检查](results/docomo_validation/README.md)：48项专项检查、701项协议检查及42项UPA/POS回归。
- [双流单元检查](results/dual_stream_unit/README.md)：54项检查。
- [运行和有效载荷格式](README_单流任务二.md)，[CPU说明](docs/CPU说明.md)，[UE说明](docs/UE说明.md)。

单流入口为run_single_stream_task2，双流完整扫描入口为run_dual_stream_task2，单配置入口为run_dual_stream_minimal，统一绘图入口为plot_precoding_results。只添加本目录，不要对整个历史副本使用addpath(genpath(...))。解压或重新运行均使用新输出目录，避免覆盖现有结果。

V3正式扫描不额外运行同算法完美CSI配对；之前V2小样本配对仅供诊断。第二流复用每AP空间波束、第一相位仅缩放，UE只增加一组相位，CPU不增加空间反馈。完整扫描未改变已验证算法，负收益比例与最差样本见新报告。

## 历史材料

6.位置反馈方案为冻结公共输入和基础依赖，本轮未修改。历史双极化多流扩展与旧single_stream_full属于此前实验；UPA_POS_V1和UPA_V2结果是修复阶段记录，不混入本次正式均值。第5、第6目录此前已建立CPU/UE相位口径，本轮恢复第8目录一致性并补齐协议，不将这些原则描述为首次提出。


最新报告的跳转已明确指向当前维护分支；MD中的AP数量图统一引用ap_ticks_5_to_9_v1版本目录，显示整数5、6、7、8、9。此次修正实际报告链接和图片引用，Word保持上一版不变。
