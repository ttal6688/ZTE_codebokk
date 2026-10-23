function [pred,diagnostic]=messages_from_estimates(net,raw,codes,active,refs,qfrequency)
% UE: split continuous geometry before encoding the direction-feedback branch.
assert(isequal(size(raw),[2 numel(refs)])&&isequal(size(codes),size(raw)));
[pcontinuous,loc]=upa.localize(net,refs,raw);
cfg=sstr.position_config(net);
assert(cfg.main_bits==36&&isequal(cfg.main_allocation,[13;14;9]));
[position_message,enc]=posfb.encode(pcontinuous,refs,cfg,36);
% CPU decoding sees only this integer message and public configuration.
pred.POS=posfb.decode(net,position_message,active,cfg);
L=2^qfrequency;k=max(0,min(L-1,round((raw+.5)*(L-1))));
hm=struct('method','HAQSE','reference_ap_ids',refs,'integer_codes',k,'q_frequency',qfrequency);
dm=struct('method','DFT','reference_ap_ids',refs,'integer_codes',codes,'q_frequency',NaN);
pred.HAQSE=upa.predict_directions(net,hm,active);
pred.DFT=upa.predict_directions(net,dm,active);
pred.DFT.method_id=sprintf('DFT_INDEX_R%d',numel(refs));
diagnostic=struct('frequency_unquantized',raw,'position_unquantized',pcontinuous,...
    'position_localization',loc,'quantizer_overflow',enc.overflow,...
    'coordinate_message',position_message,'frequency_quantization_used_for_POS',false);
end
