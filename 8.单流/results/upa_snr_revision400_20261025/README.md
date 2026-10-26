# UPA单双流400位置观测SNR更新

2026年10月25日。定位误差按观测SNR −20:10:40 dB，吞吐量按−20:5:20 dB。两类并集为11个SNR配置。每点均保留冻结位置1至400、LOS和MIX，分别给出CPU与UE结果，数据链路SNR仍固定。新增低SNR案例使用原算法，不调参或删除不利样本。

- [当前单流MD报告](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.md) · [Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.docx)
- [当前双流MD报告](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.md) · [Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.docx)

新增8个配置位于cases/snr_±XX，分别为−20、−15、−10、−5、0、5、10、15 dB。20、30、40 dB及天线数、AP数、K扫描共14个已有不同配置直接引用原[双流完整案例](../dual_stream_full400/cases)，不复制成新的独立样本。合计22个物理配置、387,200条含单双流配对的原生明细。单流使用每个案例中stream_count=1的原单流结果，并补齐LOS。

experiment_summary.csv包含全部方法的400位置均值。物理明细每个位置含CPU三种几何方法、UE六种方法和两端SVD参考、单双流共22条。CPU图中的Type-I、Type-II和Docomo复用同配置UE记录，不额外伪造CPU样本。paired_gain_summary.csv给出平均增量、最差增量和正收益比例。

localization_trials.csv.gz从实际空间消息前缀独立恢复坐标，按22个物理案例、CPU/UE、LOS/MIX保存，共105,600条。两流空间前缀完全一致，定位结果共享，不重复计算成独立试验。position_diagnostics.csv单独保留连续定位、坐标解码及越界诊断，覆盖11个SNR点及K扫描，合计12,000条；诊断使用原有连续频率到一次坐标量化的流程。

experiment_contract.json逐项记录物理参数、实际引用的数据路径及哈希。assembly_audit.json记录全部样本计数、旧单流重叠、诊断位置对应及SVD/LOS一致性。新增案例独立核验解码、功率、发送签名、有效信道、MMSE速率、第二模式及所有汇总均值；连续CPU第二相位跨实现分歧必须通过原生仅凭公共几何和比特串的严格重放。原始CSV以无损gzip发布，整数比特串的前导0保留，compression_manifest.json记录往返及哈希。

figures/single和figures/dual分别按CPU、UE保存新版本PNG和可编辑FIG。单流新增38幅，另引用原有2幅固定坐标分配图；双流74幅。定位SNR图纵轴仅标“定位误差（m）”。吞吐量为线性纵轴，从本图所有方法的最低值向下留少量余量，不强制从0开始。AP数图显示整数5、6、7、8、9，表和明细保留10。

```matlab
addpath('8.单流');
% 默认400位置。可用Worker=1..3、Workers=3分开运行互不重叠的案例。
run_snr_revision400;
run_revision_position_diagnostics;
```

```text
python 8.单流/prepare_snr_revision400.py audit-new
```

```matlab
verify_dual_stream_replay(fullfile(pwd,'8.单流','results','upa_snr_revision400_20261025'),'snr_*');
```

```text
python 8.单流/prepare_snr_revision400.py package
python 8.单流/prepare_snr_revision400.py assemble
```

```matlab
plot_snr_revision400;
verify_revision_snr_figures;
```

```text
python 8.单流/build_snr_revision_reports.py
python 8.单流/build_word_reports.py UPA单流400位置正式实验报告.md UPA单极化双流400位置完整实验报告.md
```

案例运行器不会覆盖已有结果；使用默认目录时已通过的完整同样本案例会跳过。重新运行诊断需使用新的目录或保留已有诊断，不能静默覆盖。Word按用户要求不追加检查。原20至40 dB扫描和两项32位置预实验保留为历史记录；本目录是当前正式报告的汇总入口。


后续新增的[固定B=8、R=3至8定位参考数400位置实验](../reference_ap_full400_20261025/README.md)单独保存，放在两份报告补充第一项4.1。它不覆盖本目录的协作AP数扫描、数据或图片；本目录原图保持不变。两份报告另共用新增6幅定位图，现分别为单流46幅与双流80幅插图。


后续在四组bit开销实验后各增加一张[相对Type-I的百分比图](../feedback_percentage_20261026/README.md)，不改变本目录原图和数值。两份正式报告现在分别48处、82处插图引用，新增四图也采用18 pt图例。
