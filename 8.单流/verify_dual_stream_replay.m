function audit=verify_dual_stream_replay(resultDir)
% Resolve all independently flagged continuous-optimizer differences by strict
% native replay from public geometry + wire only. No observed/truth CSI input.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
[net0,~,~]=upa.load_inputs();dirs=dir(fullfile(resultDir,'cases','case_*'));count=0;maximum=0;
for j=1:numel(dirs)
 out=fullfile(dirs(j).folder,dirs(j).name);source=fullfile(out,'CPU_continuous_replay_required.csv');
 if ~exist(source,'file'),a=jsondecode(fileread(fullfile(out,'independent_dual_audit.json')));assert(strcmp(a.status,'passed'));continue;end
 opts=detectImportOptions(source,'TextType','char');opts=setvartype(opts,'feedback_wire','char');T=readtable(source,opts);err=0;
 c=jsondecode(fileread(fullfile(out,'experiment_contract.json')));net=sstr.configure_upa(net0,c.N);active=net.active_order(1:c.B);
 for k=1:height(T)
  wire=T.feedback_wire{k};method=T.method{k};d=sstr.decode_dual(net,active,wire,method,'CPU_MODEL',c.rho_data);
  C=jsondecode(T.C_real{k})+1j*jsondecode(T.C_imag{k});e=norm(C-d.C,'fro');assert(e<1e-10);err=max(err,e);
  signature=zeros(3,2);n=(1:size(d.W,1)).';for z=1:3,signature(z,:)=(sin(.013*z*n)+1j*cos(.017*z*n)).'*d.W;end
  recorded=jsondecode(T.precoder_signature{k});assert(norm([real(signature) imag(signature)]-recorded,'fro')<1e-10);
 end
 item=struct('status','passed','flagged_records',height(T),'maximum_C_replay_error',err, ...
  'inputs','public geometry, integer wire, method, mode, public rho only','observed_or_truth_CSI_used',false);
 write_json(fullfile(out,'native_continuous_replay_audit.json'),item);count=count+height(T);maximum=max(maximum,err);
 if height(T)>0
  independent=jsondecode(fileread(fullfile(out,'independent_dual_audit.json')));independent.status='passed_with_native_replay';
  independent.native_replay=item;write_json(fullfile(out,'independent_dual_audit.json'),independent);
 end
end
audit=struct('status','passed','flagged_records',count,'maximum_C_replay_error',maximum,'cases',numel(dirs));write_json(fullfile(resultDir,'native_continuous_replay_audit.json'),audit);disp(audit);
end
function write_json(path,value)
fid=fopen(path,'w');assert(fid>0);fwrite(fid,jsonencode(value),'char');fclose(fid);
end
