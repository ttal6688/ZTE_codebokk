function audit=verify_docomo_adaptation(outputDir)
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
if nargin<1,outputDir=fullfile(root,'results','docomo_validation');end
if ~exist(outputDir,'dir'),mkdir(outputDir);end
[net0,sim,bank]=upa.load_inputs();checks=0;rows=struct([]);worst=0;replay=0;rng(20261023,'twister');
for N=[64 256 1024]
 net=sstr.configure_upa(net0,N);
 for B=[4 8 10]
  active=net.active_order(1:B);H=randn(4,N*B)+1j*randn(4,N*B);
  [msg,diag]=sstr.docomo_message(net,H,active);wire=sstr.feedback_wire('encode',net,active,msg);
  d=sstr.decode_feedback(net,active,wire,msg.method,msg.mode);power=norm(H*d.w)^2;
  assert(abs(power-diag.objective_history(end))<1e-9*max(1,power));checks=checks+1;
  drop=min(diff(diag.objective_history));assert(drop>=-1e-10*max(1,power));worst=min(worst,drop);checks=checks+1;
  assert(numel(wire)==B*net.index_bits+2*(B-1)+ceil(log2(B)));checks=checks+1;
  F=sstr.local_beams(net,msg.space.beam_indices,net.M);n=(0:B-1).';
  coeff=exp(1j*2*pi*[0;msg.space.beta_indices]/4).*exp(1j*2*pi*n*msg.space.ap_dft_index/B);
  expected=reshape(F.*coeff.',[],1)/sqrt(B);err=norm(expected-d.w);assert(err<1e-11);replay=max(replay,err);checks=checks+1;
  exact=NaN;gap=NaN;
  if B==4
   E=zeros(4,B);for b=1:B,E(:,b)=H(:,(b-1)*N+(1:N))*F(:,b);end
   V=exp(2j*pi*(0:B-1).'*(0:B-1)/B)/sqrt(B);exact=0;
   for code=0:4^(B-1)-1
    digits=mod(floor(code./4.^(0:B-2)),4);beta=exp(1j*pi/2*[0 digits]).';
    exact=max(exact,max(sum(abs(E*(beta.*V)).^2,1)));
   end
   gap=exact-power;assert(gap>=-1e-9*max(1,exact));checks=checks+1;
  end
  row=struct('N',N,'B',B,'objective_initial',diag.objective_history(1),'objective_final',power, ...
   'minimum_step_gain',drop,'fixed_beam_exhaustive_optimum',exact,'fixed_beam_gap',gap, ...
   'feedback_bits',numel(wire),'objective_history',jsonencode(diag.objective_history));
  if isempty(rows),rows=row;else,rows(end+1)=row;end %#ok<AGROW>
 end
 % Physical LOS/MIX observations: no true channel enters the optimizer.
 active=net.active_order(1:8);
 for model={'LOS','MIX'}
  sample=sstr.make_sample(net,sim,bank,399,10,model{1});[~,Hobs]=sstr.observe_sample(sample,active,30);
  [msg,diag]=sstr.docomo_message(net,Hobs,active);wire=sstr.feedback_wire('encode',net,active,msg);
  d=sstr.decode_feedback(net,active,wire,msg.method,msg.mode);
  assert(abs(norm(Hobs*d.w)^2-diag.objective_history(end))<1e-9);checks=checks+1;
 end
 assert(isequal(sstr.position_config(net),posfb.config(net)));checks=checks+1;
end
writetable(struct2table(rows),fullfile(outputDir,'docomo_objective_checks.csv'));
audit=struct('status','passed','checks',checks,'random_cases',numel(rows),'physical_LOS_MIX_cases',6, ...
 'maximum_message_replay_error',replay,'minimum_objective_step',worst, ...
 'fixed_beam_exhaustive_B',4,'exhaustive_candidates_per_case',4*4^3, ...
 'paper_source','Li Hou Chen PIMRC2024, IV25-27 and V QPSK', ...
 'scope','structural adaptation; no claim of globally optimal joint beams or full paper reproduction');
fid=fopen(fullfile(outputDir,'docomo_audit.json'),'w');assert(fid>0);fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end
