function d=decode_feedback(net,active,wire,method,mode)
% CPU interface: no observed channel, truth, or UE continuous estimates.
msg=sstr.feedback_wire('decode',net,active,wire,method,mode);B=numel(active);
space=msg.space;if strcmp(mode,'DOCOMO'),space=rmfield(space,{'beta_indices','ap_dft_index'});end
p=sstr.decode_spatial(net,active,method,space);
if strcmp(mode,'CPU_MODEL')
 H=sstr.geometry_channel(net,p.position,active);[~,~,v]=upa.principal(H);c=sstr.project_phases(p.F,v,Inf);
elseif strcmp(mode,'UE_PHASE'),c=exp(1j*2*pi*[0;msg.phase_indices(:)]/16);
else
 n=(0:B-1).';c=exp(1j*2*pi*[0;msg.space.beta_indices(:)]/4).*exp(1j*2*pi*n*msg.space.ap_dft_index/B);
end
d=struct('method_id',method,'feedback_scope','部分反馈','F',p.F,'c',c, ...
 'w',reshape(p.F.*c.',[],1)/sqrt(B),'estimated_position',p.position, ...
 'feedback_bits',numel(wire),'feedback_message',msg,'feedback_wire',wire, ...
 'space_message',space,'coordinate_bits',p.coordinate_bits,'raw_position',nan(3,1), ...
 'continuous_frequency',[],'overflow',false,'localization_condition',p.condition, ...
 'reference_AP_count',0,'geometry_parameter_count',0,'model_rows',0,'model_columns',0, ...
 'reference_observation_complex_count',0,'full_observation_complex_count',0,'shared_frontend_time_s',0,'decoder_time_s',NaN);
if ismember(method,{'TYPE_I','TYPE_II','DOCOMO_NFLOS'}),d.feedback_scope='全AP码本反馈（UE-CSI）';end
if ismember(method,{'HAQSE_R3','DFT_INDEX_R3','POS_R3'})
 d.reference_AP_count=3;d.geometry_parameter_count=6-3*strcmp(method,'POS_R3');
 d.reference_observation_complex_count=4*net.Nap*3;
 if strcmp(mode,'CPU_MODEL'),d.model_rows=4;d.model_columns=B*net.Nap;end
end
if ~strcmp(mode,'CPU_MODEL'),d.full_observation_complex_count=4*B*net.Nap;end
assert(abs(norm(d.w)^2-1)<1e-10&&max(abs(sum(abs(reshape(d.w,net.Nap,B)).^2,1)-1/B))<1e-10);
end
