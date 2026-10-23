function audit=verify_dual_stream(outputDir)
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
if nargin<1,outputDir=fullfile(root,'results','dual_stream_unit');end
if ~exist(outputDir,'dir'),mkdir(outputDir);end
checks=0;replay=0;
E=[eye(2);zeros(2)];c1=ones(2,1);rho=100;
for Q=[4 Inf]
 [c2,diag]=sstr.second_stream(E,c1,rho,Q);C=[c1 c2]/2;
 met=sstr.stream_metrics(E,C,rho);one=sstr.stream_metrics(E,c1/sqrt(2),rho);
 assert(met.SE>one.SE+1&&met.second_mode_ratio>.9);checks=checks+1;
 assert(abs(met.SE-met.joint_SE)<1e-10&&all(diff(diag.objective_history)>=-1e-9));checks=checks+1;
end
bad=[c1 c1]/2;met=sstr.stream_metrics(E,bad,rho);assert(met.second_mode_ratio<1e-20);checks=checks+1;
rng(20261023);H=randn(4,8)+1j*randn(4,8);w=randn(8,1)+1j*randn(8,1);w=w/norm(w);
met=sstr.stream_metrics(H,w,2);assert(abs(met.SE-log2(1+2*norm(H*w)^2))<1e-12);checks=checks+1;
[net0,sim,bank]=upa.load_inputs();rho=10^(sim.reference_data_SNR_dB/10)/sim.reference_power;
for N=[64 1024]
 net=sstr.configure_upa(net0,N);active=net.active_order(1:8);
 sample=sstr.make_sample(net,sim,bank,399,10,'MIX');[~,Hobs]=sstr.observe_sample(sample,active,30);
 observed=sstr.ue_designs(net,Hobs,active);
 for j=1:6
  s=observed{j};[wire,diag]=sstr.encode_dual(net,Hobs,active,s,rho);
  d=sstr.decode_dual(net,active,wire,s.method_id,s.feedback_message.mode,rho);
  assert(d.feedback_bits==s.feedback_bits+28&&isequal(s.F,d.F)&&norm(d.W(:,1)-s.w/sqrt(2))<1e-12);checks=checks+1;
  e=sstr.decode_dual(net,active,wire,s.method_id,s.feedback_message.mode,rho);err=norm(e.W-d.W,'fro');assert(err<1e-12);replay=max(replay,err);checks=checks+1;
  assert(rejects(@()sstr.decode_dual(net,active,[wire '0'],s.method_id,s.feedback_message.mode,rho)));checks=checks+1;
  if j>=4
   msg=s.feedback_message;msg.mode='CPU_MODEL';msg.phase_indices=[];cpuwire=sstr.feedback_wire('encode',net,active,msg);
   d=sstr.decode_dual(net,active,cpuwire,s.method_id,'CPU_MODEL',rho);
   assert(d.feedback_bits==s.feedback_bits-28);checks=checks+1;
   e=sstr.decode_dual(net,active,cpuwire,s.method_id,'CPU_MODEL',rho);assert(norm(e.W-d.W,'fro')<1e-12);checks=checks+1;
  end
 end
end
audit=struct('status','passed','checks',checks,'shared_spatial_beams',true,'first_column_only_power_rescaled',true, ...
 'UE_extra_bits_B8',28,'CPU_extra_feedback_bits',0,'maximum_CPU_replay_error',replay, ...
 'synthetic_two_stream_gain_verified',true,'global_phase_only_second_column_rank1_verified',true, ...
 'metric','linear-MMSE per-stream SINR and joint logdet crosscheck','holdout_sample',399);
fid=fopen(fullfile(outputDir,'dual_unit_audit.json'),'w');assert(fid>0);fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end
function yes=rejects(f)
yes=false;try,f();catch,yes=true;end
end
