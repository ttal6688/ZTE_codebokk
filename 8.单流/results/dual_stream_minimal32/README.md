# UPA单极化双流32位置最小验证

位置1至32，LOS/MIX分开。1,408条记录、704组含SVD配对、576组可实施配对。每AP共享空间波束，第二流只新增相位。CPU与UE各7组图。

- [原始记录](dual_stream_trials.csv)
- [汇总](dual_stream_summary.csv)
- [配对](single_dual_pairs.csv)
- [可行性统计](method_feasibility_summary.csv)
- [独立审计](independent_dual_audit.json)
- [配置](experiment_contract.json)
- [运行检查](audit.json)
- [源码输入哈希](source_and_input_SHA256.json)
- [扩展报告](../../docs/UPA单极化双流扩展验证报告.md)

双流SVD是等功率参考，不称为一般容量上界。未运行完整双流扫描。

| CPU图 | UE图 |
|---|---|
| [LOS_单双流吞吐量](CPU/CPU_LOS_单双流吞吐量.png) | [LOS_单双流吞吐量](UE/UE_LOS_单双流吞吐量.png) |
| [MIX_单双流吞吐量](CPU/CPU_MIX_单双流吞吐量.png) | [MIX_单双流吞吐量](UE/UE_MIX_单双流吞吐量.png) |
| [MIX_第二模式CDF](CPU/CPU_MIX_第二模式CDF.png) | [MIX_第二模式CDF](UE/UE_MIX_第二模式CDF.png) |
| [MIX_速率增量CDF](CPU/CPU_MIX_速率增量CDF.png) | [MIX_速率增量CDF](UE/UE_MIX_速率增量CDF.png) |
| [单双流反馈量](CPU/CPU_单双流反馈量.png) | [单双流反馈量](UE/UE_单双流反馈量.png) |
