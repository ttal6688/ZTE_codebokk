# 固定8个协作AP的400位置定位参考数扫描

本实验是两份正式报告中“4 额外补充”的第一个实验4.1。协作AP数B固定8，仅改变定位参考／反馈AP数R=3、4、5、6、7、8。原固定R=3、改变协作AP总数的正文定位误差、反馈量等实验完整保留，不覆盖或替换原图及明细。

- [单流正式报告及本补充](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.md#41-固定8个协作ap的定位参考数扫描) · [Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.docx)
- [双流正式报告及本补充](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.md#41-固定8个协作ap的定位参考数扫描) · [Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.docx)

设置：全部400个冻结位置，每AP32×32单极化UPA，观测SNR 30 dB；纯LOS和MIX分别运行，MIX的K=10 dB。每个位置和信道只生成一次完整8 AP观测，固定噪声方差，按预先公开AP顺序逐步使用前R个AP。估计值跨R复用，未按结果选择AP或重采噪声。

空间频率和DFT索引分别打包R个AP的方向消息，再解码定位；位置反馈用R个AP的连续频率直接定位，再按13/14/9 bit量化一次坐标，始终仅发送一份36 bit位置。实际空间消息分别为28R、14R、36 bit。此处不含相位字段，不将参考AP观测或计算成本计作零。

保存14,400条物理定位记录及6,400条AP估计记录；每个信道、方法、R有400个不同位置。单双流、CPU及UE共享这个定位前端，所以只保存一份物理结果，在各自报告中明确共用，不伪造四份独立试验。LOC_REF_SWEEP_V1仅为本定位诊断的消息格式，完整SSTR_V2预编码及正文吞吐量／通信反馈实验仍固定R=3，没有扩成R=8。

localization_trials.csv.gz含参考集合、真实／恢复／连续坐标、误差、实际整数比特串、消息长度、噪声方差及越界信息；ap_estimates.csv.gz含每个AP一次性估计的连续频率和DFT索引。localization_summary.csv含均值、中位数、95%分位和空间反馈量。原始CSV无损压缩，整数前导0保留，往返及哈希见compression_manifest.json。

独立Python程序逐条恢复整数消息、定位坐标、误差及全部统计。R=3与当前400位置正式数据的2,400条误差逐条对齐；原32位置预实验所有R的1,152条消息及误差也逐条对齐。审计见independent_localization_audit.json，图形对应关系见figure_audit.json，源文件及冻结输入指纹见source_and_input_SHA256.json。

figures/CPU及figures/UE各保存LOS、MIX的定位误差图；figures/diagnostics另保存两种信道的坐标量化前后图。共6组PNG及可编辑FIG，由两份正式报告共享。横轴仅显示整数3至8，纵轴名称仅为定位误差及单位。完整报告现为单流46幅插图、双流80幅插图，其中本实验6幅在两份报告中共用。

均值改善不保证每个位置或每个中间R都改善。固定嵌套顺序同时改变方向观测及AP几何，不能推广为任意AP子集的结论。findings.json同时给出R=3至8均值降幅与逐位置严格改善比例。

```matlab
addpath('8.单流');
run_reference_ap_full400; % 默认1:400，独立新目录，不覆盖既有数据
```

```text
python 8.单流/analyze_reference_ap_pilot.py results/reference_ap_full400_20261025 --stage audit
python 8.单流/report_reference_ap_full400.py
```

```matlab
plot_reference_ap_full400;
```

```text
python 8.单流/build_snr_revision_reports.py
python 8.单流/build_word_reports.py UPA单流400位置正式实验报告.md UPA单极化双流400位置完整实验报告.md
```

需要重新仿真时给run_reference_ap_full400指定新的OutputDir；既有结果不静默覆盖。原32位置预实验保留。两份Word沿用既有样式，按用户要求不追加检查。


后续在四组bit开销实验后各增加一张[相对Type-I的百分比图](../feedback_percentage_20261026/README.md)，不改变本目录原图和数值。两份正式报告现在分别48处、82处插图引用，新增四图也采用18 pt图例。
