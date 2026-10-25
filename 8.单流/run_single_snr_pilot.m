function audit=run_single_snr_pilot(varargin)
% Small low-to-high observation-SNR experiment using the existing single-stream algorithms.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');
addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
p=inputParser;addParameter(p,'OutputDir',fullfile(root,'results','single_stream_snr_pilot32_20261025'));
addParameter(p,'ResumeControls',false,@islogical);
parse(p,varargin{:});out=char(p.Results.OutputDir);
ids=round(linspace(1,400,32));snrs=[-20 -10 0 10 20 30 40];
if p.Results.ResumeControls
 saved=jsondecode(fileread(fullfile(out,'experiment_contract.json')));
 assert(isequal(saved.sample_ids(:),ids(:))&&isequal([saved.settings.SNRdB],snrs));
 assert(all([saved.settings.Nant]==1024)&&all([saved.settings.B]==8)&&all([saved.settings.KdB]==10)&&saved.include_CSI_pairs);
 assert(isequal(sort(string(saved.channel_models(:))),sort(["LOS";"MIX"])));
 audit=jsondecode(fileread(fullfile(out,'audit.json')));assert(strcmp(audit.status,'passed'));
 fprintf('Reusing completed SNR scan; creating missing controls only.\n');
else
 audit=run_single_stream_task2('Mode','full','SampleIds',ids,'ObservationSNRs',snrs, ...
  'ChannelModels',{'LOS','MIX'},'IncludeCSIPairs',true,'MakeFigures',false,'OutputDir',out);
end
assert(~exist(fullfile(out,'noisefree_control_trials.csv'),'file'),'Control results already exist');

% UE perfect-CSI rows already use exactly Htrue, without rerunning a new estimator.
% Recover the CPU control only from those spatial messages and public geometry.
opts=detectImportOptions(fullfile(out,'single_stream_trials.csv'),'TextType','string');
opts=setvartype(opts,'feedback_wire','string');T=readtable(fullfile(out,'single_stream_trials.csv'),opts);
Q=T(T.branch=="UE"&T.csi=="PERFECT"&T.x_value==snrs(1),:);
C=[Q;T(T.csi=="IDEAL"&T.x_value==snrs(1),:)];
[net0,sim,bank]=upa.load_inputs();net=sstr.configure_upa(net0,1024);active=net.active_order(1:8);
rho=10^(sim.reference_data_SNR_dB/10)/sim.reference_power;
for model=["LOS" "MIX"]
 for sid=ids
  sample=sstr.make_sample(net,sim,bank,sid,10,char(model));[Htrue,~]=sstr.observe_sample(sample,active,Inf);
  for method=["HAQSE_R3" "DFT_INDEX_R3" "POS_R3"]
   row=Q(Q.channel_model==model&Q.sample_id==sid&Q.method==method,:);
   msg=sstr.feedback_wire('decode',net,active,char(row.feedback_wire),char(method),'UE_PHASE');
   msg.mode='CPU_MODEL';msg.phase_indices=[];
   wire=sstr.feedback_wire('encode',net,active,msg);d=sstr.decode_feedback(net,active,wire,msg.method,msg.mode);
   row.branch="CPU";row.role="CPU_METHOD";row.feedback_wire=string(wire);row.feedback_message=string(jsonencode(msg));
   row.feedback_bits=numel(wire);row.space_message=string(jsonencode(d.space_message));
   power=norm(Htrue*d.w)^2;row.received_power=power;row.normalized_power_gain=power/row.ideal_received_power;
   row.spectral_efficiency=log2(1+rho*power);row.throughput_Mbps=400*row.spectral_efficiency;
   row.position_error_m=norm(d.estimated_position-sample.position);
   row.estimated_x_m=d.estimated_position(1);row.estimated_y_m=d.estimated_position(2);row.estimated_z_m=d.estimated_position(3);
   row.AP_coefficients=string(jsonencode([real(d.c) imag(d.c)]));row.precoder_signature=string(signature(d.w));
   row.maximum_AP_power_error=max(abs(sum(abs(reshape(d.w,net.Nap,8)).^2,1)-1/8));
   row.full_observation_complex_count=0;row.model_rows=4;row.model_columns=8*net.Nap;
   C=[C;row]; %#ok<AGROW>
  end
 end
end
C.curve(:)="NOISE_FREE";C.x_value(:)=0;C.observation_SNR_dB(:)=Inf;
writetable(C,fullfile(out,'noisefree_control_trials.csv'));
keys={'branch','role','csi','channel_model','method'};[g,S]=findgroups(C(:,keys));
S.samples=splitapply(@numel,C.sample_id,g);
for field={'position_error_m','raw_position_error_m','throughput_Mbps','spectral_efficiency','feedback_bits'}
 S.(['mean_' field{1}])=splitapply(@(x)mean(x,'omitnan'),C.(field{1}),g);
end
writetable(S,fullfile(out,'noisefree_control_summary.csv'));
contract=struct('scope','32-position diagnostic only; existing400-position results unchanged', ...
 'sample_ids',ids,'selection','round(linspace(1,400,32)); before observing results', ...
 'observation_SNR_dB',snrs,'channels',{{'LOS','MIX'}},'Nant',1024,'B',8,'K_dB',10, ...
 'reference_data_SNR_dB',sim.reference_data_SNR_dB,'rho_data',rho,'bandwidth_Hz',400e6, ...
 'noise','one original frozen noise matrix per position and physical AP, scaled across SNR', ...
 'noise_free','same methods on exact Htrue; CPU uses only perfect spatial payload and public geometry; evaluation alone uses Htrue', ...
 'independent_noise_repetitions',1,'main_records',height(T),'control_records',height(C));
fid=fopen(fullfile(out,'pilot_contract.json'),'w','n','UTF-8');fprintf(fid,'%s',jsonencode(contract));fclose(fid);
disp('LOW_TO_HIGH_SNR_PILOT_COMPLETE');
end

function value=signature(w)
n=(1:numel(w)).';z=zeros(3,1);
for j=1:3,z(j)=(sin(.013*j*n)+1j*cos(.017*j*n)).'*w;end
value=jsonencode([real(z) imag(z)]);
end
