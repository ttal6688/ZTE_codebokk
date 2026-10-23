# UPA单流修复流程验证

本目录为UPA单极化单流小样本验证，只有104条记录，样本位置[399, 400]。不是400位置正式实验，不作性能排名。

覆盖8×8、16×16、32×32和多个协作AP数量；带宽按400 MHz换算。POS由连续HAQSE频率定位后仅量化坐标，公开分配13/14/9 bit。

- [原始记录](single_stream_trials.csv)
- [分组均值](single_stream_summary.csv)
- [运行配置](experiment_contract.json)
- [运行检查](audit.json)
- [独立整数消息及反馈审计](independent_message_audit.json)
- [源码与输入校验](source_and_input_SHA256.json)
- [实现与验证说明](../../docs/UPA与位置反馈修复说明.md)

独立重放48条几何空间消息，其中POS有16条。CPU与UE使用相同POS消息；量化前位置由连续频率重新定位后核对。所有有限反馈记录按对应UPA尺寸重新核算bit。
