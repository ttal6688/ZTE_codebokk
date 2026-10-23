function audit=run_dual_stream_minimal(varargin)
% UPA single-polarization 1/2-stream pairs. No second spatial beam is introduced.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
p=inputParser;addParameter(p,'SampleIds',1:32);addParameter(p,'OutputDir',fullfile(root,'results','dual_stream_minimal32'));parse(p,varargin{:});opt=p.Results;
sampleIds=opt.SampleIds;assert(all(ismember(sampleIds,1:400))&&numel(unique(sampleIds))==numel(sampleIds));out=char(opt.OutputDir);
assert(~exist(fullfile(out,'dual_stream_trials.csv'),'file'),'Use a new output directory');if ~exist(out,'dir'),mkdir(out);end
[net0,sim,bank]=upa.load_inputs();net=sstr.configure_upa(net0,1024);active=net.active_order(1:8);B=8;N=1024;
rho=10^(sim.reference_data_SNR_dB/10)/sim.reference_power;rows=cell(0,1);started=tic;
for model={'LOS','MIX'}
 channel=model{1};
 for sid=sampleIds
  sample=sstr.make_sample(net,sim,bank,sid,10,channel);[Htrue,Hobs]=sstr.observe_sample(sample,active,30);
  [~,sv,V]=svd(Htrue,'econ');sv=diag(sv);truthratio=sv(2)^2/sv(1)^2;UE=sstr.ue_designs(net,Hobs,active);
  for branch={'CPU','UE'}
   panel=branch{1};
   % Equal-power rank2 SVD is a reference, not arbitrary-power capacity.
   for ns=1:2,rows{end+1}=record('IDEAL_SVD',V(:,1:ns)/sqrt(ns),[],[],[],NaN,struct,'IDEAL_REFERENCE',ns);end %#ok<AGROW>
   if strcmp(panel,'CPU'),methods=4:6;else,methods=1:6;end
   for j=methods
    single=UE{j};
    if strcmp(panel,'CPU')
     msg=single.feedback_message;msg.mode='CPU_MODEL';msg.phase_indices=[];
     wire=sstr.feedback_wire('encode',net,active,msg);single=sstr.decode_feedback(net,active,wire,msg.method,msg.mode);
     dual=sstr.decode_dual(net,active,wire,msg.method,'CPU_MODEL',rho);diagnostic=dual.diagnostic;
    else
     [wire,diagnostic]=sstr.encode_dual(net,Hobs,active,single,rho);
     dual=sstr.decode_dual(net,active,wire,single.method_id,single.feedback_message.mode,rho);
    end
    assert(isequal(single.F,dual.F)&&norm(dual.W(:,1)-single.w/sqrt(2))<1e-12);
    Et=sstr.effective_channel(Htrue,single.F);se=svd(Et,'econ');subratio=se(2)^2/max(se(1)^2,realmin);
    rows{end+1}=record(single.method_id,single.w,single.F,single.c/sqrt(B),Et,single.feedback_bits,single.feedback_message,'OBSERVED',1); %#ok<AGROW>
    rows{end+1}=record(single.method_id,dual.W,dual.F,dual.C,Et,dual.feedback_bits,single.feedback_message,'OBSERVED',2); %#ok<AGROW>
    rows{end}.feedback_wire=wire;rows{end}.design_objective_history=jsonencode(diagnostic.objective_history);
    rows{end-1}.feedback_wire=single.feedback_wire;rows{end}.subspace_second_mode_ratio=subratio;rows{end-1}.subspace_second_mode_ratio=subratio;
   end
  end
  fprintf('Dual minimal %s sample %d, %.1f s\n',channel,sid,toc(started));
 end
end
T=struct2table(vertcat(rows{:}));writetable(T,fullfile(out,'dual_stream_trials.csv'));
keys={'branch','channel_model','method','stream_count','csi'};[g,S]=findgroups(T(:,keys));S.samples=splitapply(@numel,T.sample_id,g);
for field={'throughput_Mbps','joint_throughput_Mbps','second_mode_ratio','subspace_second_mode_ratio','feedback_bits','true_channel_second_mode_ratio'}
 S.(['mean_' field{1}])=splitapply(@(x)mean(x,'omitnan'),T.(field{1}),g);
end
writetable(S,fullfile(out,'dual_stream_summary.csv'));
keys={'branch','channel_model','method','sample_id'};A=T(T.stream_count==1,:);D=T(T.stream_count==2,:);
A=renamevars(A(:,[keys {'throughput_Mbps','feedback_bits'}]),{'throughput_Mbps','feedback_bits'},{'single_Mbps','single_bits'});
D=renamevars(D(:,[keys {'throughput_Mbps','feedback_bits','second_mode_ratio'}]),{'throughput_Mbps','feedback_bits'},{'dual_Mbps','dual_bits'});
P=innerjoin(A,D,'Keys',keys);P.delta_Mbps=P.dual_Mbps-P.single_Mbps;P.extra_bits=P.dual_bits-P.single_bits;
writetable(P,fullfile(out,'single_dual_pairs.csv'));
contract=struct('version','UPA_SINGLEPOL_DUAL_MINIMAL_V1','sample_ids',sampleIds,'N',N,'B',B,'observation_SNR_dB',30,'K_dB',10, ...
 'channel_models',{{'LOS','MIX'}},'bandwidth_Hz',400e6,'rho_data',rho, ...
 'shared_F',true,'second_stream','new per-AP relative phases only, no new spatial beam', ...
 'power','C=[c1 c2]/sqrt(2B), each AP total1/B','phase_optimizer','residual+DFT-ramp seeds,3sweeps,UE4bit,CPU64grid+24golden', ...
 'CPU_inputs','public geometry+spatial bits; no observed/truth channel','UE_inputs','observed CSI+decoded shared F', ...
 'Docomo','same single-stream structure adaptation, plus general 4bit second-phase profile; not paper multi-rank DFT subset reproduction', ...
 'CSI','only OBSERVED implementable methods; perfect CSI SVD references separate', ...
 'SVD','equal-power rank1/rank2 reference under total power; rank2 is not general waterfilled capacity upper bound');
write_json(fullfile(out,'experiment_contract.json'),contract);
audit=struct('status','passed','positions',numel(sampleIds),'sample_ids',sampleIds,'records',height(T),'single_dual_pairs',height(P), ...
 'elapsed_seconds',toc(started),'full_dual_scan',false,'total_power',1,'per_AP_power',1/B);
write_json(fullfile(out,'audit.json'),audit);disp(audit);
 function row=record(method,W,F,C,Et,bits,msg,csi,ns)
  metric=sstr.stream_metrics(Htrue,W,rho);signature=zeros(3,ns);n=(1:size(W,1)).';
  for z=1:3,signature(z,:)=(sin(.013*z*n)+1j*cos(.017*z*n)).'*W;end
  maxpower=NaN;
  if ~isempty(F)
   power=zeros(1,B);for b=1:B,power(b)=norm(W((b-1)*N+(1:N),:),'fro')^2;end
   maxpower=max(abs(power-1/B));assert(maxpower<1e-10&&abs(norm(W,'fro')^2-1)<1e-10);
  end
  row=struct('branch',panel,'channel_model',channel,'sample_id',sid,'method',method,'stream_count',ns,'csi',csi, ...
   'B',B,'antenna_count',N,'UPA_side',32,'array','UPA','throughput_Mbps',400*metric.SE, ...
   'joint_throughput_Mbps',400*metric.joint_SE,'spectral_efficiency',metric.SE,'joint_SE',metric.joint_SE, ...
   'SINR',jsonencode(metric.SINR),'singular_values',jsonencode(metric.singular_values), ...
   'second_mode_ratio',metric.second_mode_ratio,'subspace_second_mode_ratio',NaN,'true_channel_second_mode_ratio',truthratio, ...
   'feedback_bits',bits,'feedback_message',jsonencode(msg),'feedback_wire','','C_real',jsonencode(real(C)),'C_imag',jsonencode(imag(C)), ...
   'effective_true_channel_real',jsonencode(real(Et)),'effective_true_channel_imag',jsonencode(imag(Et)), ...
   'precoder_signature',jsonencode([real(signature) imag(signature)]),'design_objective_history','[]', ...
   'maximum_AP_power_error',maxpower,'total_power',norm(W,'fro')^2);
 end
end
function write_json(path,value)
fid=fopen(path,'w');assert(fid>0);fwrite(fid,jsonencode(value),'char');fclose(fid);
end
