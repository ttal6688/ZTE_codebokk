function audit=run_single_stream_task2(varargin)
% UPA / single polarization / single stream. All usable precoders decode payloads.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');
addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
p=inputParser;addParameter(p,'Mode','smoke',@(x)ismember(x,{'smoke','verify','full'}));
addParameter(p,'OutputDir','');addParameter(p,'Samples',[],@(x)isempty(x)||(isscalar(x)&&x>=1&&x<=400));
addParameter(p,'MakeFigures',true,@islogical);addParameter(p,'ChannelModels',{});parse(p,varargin{:});opt=p.Results;
[net0,sim,bank]=upa.load_inputs();sim.bandwidth_Hz=400e6;
sim.rho_data=10^(sim.reference_data_SNR_dB/10)/sim.reference_power;assert(sim.UE_phase_bits==4&&sim.frequency_bits_per_dimension==14);
if isempty(opt.OutputDir),out=fullfile(root,'results',['single_stream_UPA_V2_' opt.Mode]);else,out=char(opt.OutputDir);end
assert(~exist(fullfile(out,'single_stream_trials.csv'),'file'),'sstr:ExistingResults','Use a new OutputDir');
if ~exist(out,'dir'),mkdir(out);end
if isempty(opt.Samples)
 if strcmp(opt.Mode,'full'),sampleIds=1:400;elseif strcmp(opt.Mode,'verify'),sampleIds=[399 400];else,sampleIds=1:4;end
else,sampleIds=1:round(opt.Samples);end
models=opt.ChannelModels;if isempty(models),if strcmp(opt.Mode,'verify'),models={'LOS','MIX'};else,models={'MIX'};end,end
assert(iscell(models)&&all(ismember(models,{'LOS','MIX'})));
settings=make_settings(opt.Mode);rows=cell(0,1);started=tic;replays=0;maxReplay=0;
for si=1:numel(settings)
 q=settings(si);net=sstr.configure_upa(net0,q.Nant);active=net.active_order(1:q.B);
 for mi=1:numel(models)
  model=models{mi};
  for sid=sampleIds
   sample=make_sample(net,sim,bank,sid,q.KdB,model);[Htrue,Hobs]=observe_sample(sample,active,q.SNRdB);
   [~,s2,vtrue]=upa.principal(Htrue);ideal=struct('w',vtrue,'s2',s2);
   [observed,rc,err]=ue_designs(net,Hobs,active);replays=replays+rc;maxReplay=max(maxReplay,err);
   [perfect,rc,err]=ue_designs(net,Htrue,active);replays=replays+rc;maxReplay=max(maxReplay,err);
   % CPU has only decoded spatial payload + public geometry. Hobs is not passed.
   cpu=cell(1,3);
   for j=1:3
    src=observed{j+3};msg=src.feedback_message;msg.mode='CPU_MODEL';msg.phase_indices=[];
    wire=sstr.feedback_wire('encode',net,active,msg);clock=tic;cpu{j}=sstr.decode_feedback(net,active,wire,msg.method,msg.mode);
    cpu{j}.decoder_time_s=toc(clock);cpu{j}=copy_diagnostics(cpu{j},src);replays=replays+1;
   end
   for branch={'CPU','UE'}
    name=branch{1};rows{end+1}=record(ideal,'IDEAL',name,'UPPER_BOUND'); %#ok<AGROW>
    if strcmp(name,'CPU')
     for j=1:2,rows{end+1}=record(observed{j},'OBSERVED',name,'UE_REFERENCE');end %#ok<AGROW>
     for j=1:3,rows{end+1}=record(cpu{j},'OBSERVED',name,'CPU_METHOD');end %#ok<AGROW>
    else
     for j=1:6,rows{end+1}=record(observed{j},'OBSERVED',name,'UE_METHOD');end %#ok<AGROW>
     for j=1:6,rows{end+1}=record(perfect{j},'PERFECT',name,'UE_METHOD');end %#ok<AGROW>
    end
   end
  end
 end
 fprintf('UPA V2: %s %d/%d, %.1f s\n',q.curve,si,numel(settings),toc(started));
end
T=struct2table(vertcat(rows{:}));writetable(T,fullfile(out,'single_stream_trials.csv'));
S=summarize(T);writetable(S,fullfile(out,'single_stream_summary.csv'));
P=paired_csi(T);writetable(P,fullfile(out,'paired_CSI.csv'));
contract=struct('version','UPA_SINGLE_PROTOCOL_V2','task','UPA单极化单流', ...
 'baseline_selection','joint right singular mode; Type-II same orthogonal group, amplitude3/relativephase2', ...
 'phase_rule','joint-mode projection, UE relative phases quantized4, AP1 anchor0; CPU continuous model projection', ...
 'CPU_information','public geometry and spatial payload only; no reference measured channel blocks', ...
 'UE_information','all-active-AP CSI at UE, decoded spatial beams, phase feedback', ...
 'CSI_pair','same algorithm/codebook/payload/power, observed versus perfect; no guaranteed per-sample monotonicity', ...
 'POS_input','continuous HAQSE -> UE localization -> coordinate quantization only','POS_coordinate_bits',[13 14 9], ...
 'POS_ROI_lo',[19 19 -1],'POS_ROI_hi',[31 31 6],'POS_allocation','frozen public relative-phase sensitivity, no position-adaptive header', ...
 'payload_accounting','MSB-first packed integer payload; method/config/AP order public; transport headers/FEC excluded for all methods', ...
 'reference_AP_ids',net0.reference3,'sample_ids',sampleIds,'settings',settings,'channel_models',{models}, ...
 'bandwidth_Hz',sim.bandwidth_Hz,'rho_data',sim.rho_data,'reference_data_SNR_dB',sim.reference_data_SNR_dB, ...
 'reference_power',sim.reference_power,'timing_note','decoder_time measures decoder only; UE shared frontend timed per family and repeated, not standalone method complexity', 'bandwidth_model','narrowband SE times 400 MHz; no OFDM or bandwidth-dependent thermal noise', ...
 'CPU_cost','R and geometry-message dimension fixed; observations scale with N, model4xBN and work scale with B,N; pilot symbols not modeled', ...
 'Docomo','structure adaptation only, QPSK beta + AP DFT + three alternating updates; not verified original reproduction', ...
 'ideal','true joint SVD, total power1, relaxed per-AP equal-power constraint', ...
 'elapsed_seconds',toc(started));write_json(fullfile(out,'experiment_contract.json'),contract);
if opt.MakeFigures,plot_single_stream_task2(out);end
audit=struct('status','passed','records',height(T),'sample_ids',sampleIds,'positions',numel(sampleIds), ...
 'settings',numel(settings),'channel_models',{models},'complete_payload_replays',replays, ...
 'maximum_UE_vs_wire_precoder_error',maxReplay,'paired_CSI_records',height(P), ...
 'POS_overflow_records',sum(T.quantizer_overflow),'elapsed_seconds',toc(started),'full400',isequal(sampleIds,1:400));
write_json(fullfile(out,'audit.json'),audit);disp(audit);
 function row=record(d,csi,branch,role)
  isideal=strcmp(csi,'IDEAL');power=norm(Htrue*d.w)^2;se=log2(1+sim.rho_data*power);
  assert(abs(norm(d.w)^2-1)<1e-9&&power<=s2*(1+1e-8));
  row=struct('branch',branch,'role',role,'csi',csi,'channel_model',model, ...
   'curve',q.curve,'x_value',q.xvalue,'B',q.B,'antenna_count',q.Nant,'UPA_side',net.Nside, ...
   'array','UPA','observation_SNR_dB',q.SNRdB,'Rician_K_dB',q.KdB,'sample_id',sid, ...
   'method','','feedback_scope','','position_error_m',NaN,'raw_position_error_m',NaN, ...
   'throughput_Mbps',400*se,'spectral_efficiency',se,'received_power',power, ...
   'ideal_received_power',s2,'normalized_power_gain',power/s2,'feedback_bits',NaN, ...
   'coordinate_bits_x',NaN,'coordinate_bits_y',NaN,'coordinate_bits_z',NaN, ...
   'true_x_m',sample.position(1),'true_y_m',sample.position(2),'true_z_m',sample.position(3), ...
   'estimated_x_m',NaN,'estimated_y_m',NaN,'estimated_z_m',NaN, ...
   'position_before_coordinate_quantization','[]','frequency_unquantized','[]','space_message','{}', ...
   'feedback_message','{}','feedback_wire','','quantizer_overflow',false, ...
   'reference_AP_count',0,'geometry_parameter_count',0,'model_rows',0,'model_columns',0, ...
   'reference_observation_complex_count',0,'full_observation_complex_count',0,'shared_frontend_time_s',0,'decoder_time_s',NaN, ...
   'AP_coefficients','[]','precoder_signature',signature(d.w),'maximum_AP_power_error',NaN);
  if isideal,row.method='IDEAL_SVD';row.feedback_scope='理想上界';return;end
  row.method=d.method_id;row.feedback_scope=d.feedback_scope;row.feedback_bits=d.feedback_bits;
  if all(isfinite(d.estimated_position)),row.position_error_m=norm(d.estimated_position-sample.position);end
  if all(isfinite(d.raw_position)),row.raw_position_error_m=norm(d.raw_position-sample.position);end
  row.coordinate_bits_x=d.coordinate_bits(1);row.coordinate_bits_y=d.coordinate_bits(2);row.coordinate_bits_z=d.coordinate_bits(3);
  row.estimated_x_m=d.estimated_position(1);row.estimated_y_m=d.estimated_position(2);row.estimated_z_m=d.estimated_position(3);
  row.position_before_coordinate_quantization=jsonencode(d.raw_position);row.frequency_unquantized=jsonencode(d.continuous_frequency);
  row.space_message=jsonencode(d.space_message);row.feedback_message=jsonencode(d.feedback_message);row.feedback_wire=d.feedback_wire;
  row.quantizer_overflow=d.overflow;row.AP_coefficients=jsonencode([real(d.c) imag(d.c)]);
  for key={'reference_AP_count','geometry_parameter_count','model_rows','model_columns', ...
    'reference_observation_complex_count','full_observation_complex_count','shared_frontend_time_s','decoder_time_s'}
   row.(key{1})=d.(key{1});
  end
  row.maximum_AP_power_error=max(abs(sum(abs(reshape(d.w,net.Nap,q.B)).^2,1)-1/q.B));
 end
end
function [designs,count,maxerr]=ue_designs(net,H,active)
clock=tic;[m1,m2,detail]=sstr.baseline_messages(net,H,active);baseTime=toc(clock);
clock=tic;md=sstr.docomo_message(net,H,active);docTime=toc(clock);
clock=tic;[pred,diag]=sstr.space_messages(net,H,active,net.reference3,14);geoTime=toc(clock);
messages={m1,m2,md};items={pred.HAQSE,pred.DFT,pred.POS};[~,~,v]=upa.principal(H);
for j=1:3
 item=items{j};[~,phase]=sstr.project_phases(item.F,v,4);
 messages{end+1}=struct('protocol','SSTR_V2','method',item.method_id,'mode','UE_PHASE', ...
  'space',item.direction_message,'phase_indices',phase); %#ok<AGROW>
end
designs=cell(1,6);maxerr=0;count=0;
for j=1:6
 clock=tic;msg=messages{j};wire=sstr.feedback_wire('encode',net,active,msg);
 clock=tic;d=sstr.decode_feedback(net,active,wire,msg.method,msg.mode);decodeTime=toc(clock);
 if j<=2
  if j==1,F=detail.F1;else,F=detail.F2;end
  c=sstr.project_phases(F,detail.target,4);
 elseif j>=4,F=items{j-3}.F;c=sstr.project_phases(F,v,4);
 else
  F=d.F;B=numel(active);c=exp(1j*2*pi*[0;msg.space.beta_indices]/4).*exp(1j*2*pi*(0:B-1).'*msg.space.ap_dft_index/B);
 end
 w=reshape(F.*c.',[],1)/sqrt(numel(active));err=norm(w-d.w);assert(err<1e-11);maxerr=max(maxerr,err);count=count+1;
 d.decoder_time_s=decodeTime;
 if j<=2,d.shared_frontend_time_s=baseTime;elseif j==3,d.shared_frontend_time_s=docTime;else
  d.shared_frontend_time_s=geoTime;d.continuous_frequency=diag.frequency_unquantized;
  if j==6,d.raw_position=diag.position_unquantized;d.overflow=diag.quantizer_overflow;else,d.raw_position=d.estimated_position;end
 end
 designs{j}=d;
end
end
function d=copy_diagnostics(d,src)
d.raw_position=src.raw_position;d.continuous_frequency=src.continuous_frequency;d.overflow=src.overflow;
end
function value=signature(w)
n=(1:numel(w)).';z=zeros(3,1);
for j=1:3,z(j)=(sin(.013*j*n)+1j*cos(.017*j*n)).'*w;end
value=jsonencode([real(z) imag(z)]);
end
function settings=make_settings(mode)
settings=struct('curve',{},'xvalue',{},'Nant',{},'B',{},'SNRdB',{},'KdB',{});
if strcmp(mode,'verify')
 settings=[item('SNR',30,64,5,30,10),item('SNR',30,256,8,30,10), ...
 item('SNR',30,1024,8,30,10),item('SNR',30,1024,10,30,10)];return;
end
if strcmp(mode,'full'),snrs=20:5:40;aps=5:10;ks=0:5:20;else,snrs=[20 30 40];aps=[5 8 10];ks=[0 10 20];end
for x=snrs,settings(end+1)=item('SNR',x,1024,8,x,10);end
for x=[64 256 1024],settings(end+1)=item('天线数',x,x,8,30,10);end
for x=aps,settings(end+1)=item('AP数',x,1024,x,30,10);end
for x=ks,settings(end+1)=item('莱斯因子',x,1024,8,30,x);end
end
function q=item(curve,x,N,B,SNR,K)
q=struct('curve',curve,'xvalue',x,'Nant',N,'B',B,'SNRdB',SNR,'KdB',K);
end
function sample=make_sample(net,sim,bank,sid,KdB,model)
p=bank.positions(:,sid);scatter=sim.scatterer_positions_m.';sample.position=p;
sample.H=zeros(4,net.Nap,10);sample.Z=sample.H;K=10^(KdB/10);
for b=1:10
 ap=net.ap_elements(:,:,b);los=zeros(4,net.Nap);nlos=los;
 for u=1:4
  user=p+net.ue_offsets(:,u);r=vecnorm(ap-user);los(u,:)=exp(-1j*net.k*r)./r;
  for ell=1:6,L=vecnorm(ap-scatter(:,ell))+norm(scatter(:,ell)-user);nlos(u,:)=nlos(u,:)+bank.zeta(sid,ell)*exp(-1j*net.k*L)./L;end
 end
 if strcmp(model,'LOS'),sample.H(:,:,b)=los;else
  nlos=nlos*norm(los,'fro')/norm(nlos,'fro');sample.H(:,:,b)=sqrt(K/(K+1))*los+sqrt(1/(K+1))*nlos;
 end
 rng(bank.noise_seed(sid,b),'twister');sample.Z(:,:,b)=(randn(4,net.Nap)+1j*randn(4,net.Nap))/sqrt(2);
end
end
function [Htrue,Hobs]=observe_sample(sample,ids,snr)
Htrue=reshape(sample.H(:,:,ids),4,[]);Z=reshape(sample.Z(:,:,ids),4,[]);
Hobs=Htrue+sqrt(mean(abs(Htrue(:)).^2)/10^(snr/10))*Z;
end
function S=summarize(T)
keys={'branch','role','csi','channel_model','curve','x_value','method','feedback_scope', ...
 'B','antenna_count','observation_SNR_dB','Rician_K_dB'};
[g,S]=findgroups(T(:,keys));S.samples=splitapply(@numel,T.sample_id,g);
for field={'position_error_m','raw_position_error_m','throughput_Mbps','spectral_efficiency','received_power','feedback_bits', ...
 'reference_AP_count','geometry_parameter_count','model_rows','model_columns','reference_observation_complex_count', ...
 'full_observation_complex_count','shared_frontend_time_s','decoder_time_s','quantizer_overflow'}
 S.(['mean_' field{1}])=splitapply(@(x)mean(x,'omitnan'),double(T.(field{1})),g);
end
end
function P=paired_csi(T)
keys={'channel_model','curve','x_value','B','antenna_count','observation_SNR_dB','Rician_K_dB','sample_id','method'};
a=T(strcmp(T.branch,'UE')&strcmp(T.csi,'OBSERVED'),:);b=T(strcmp(T.branch,'UE')&strcmp(T.csi,'PERFECT'),:);
a=renamevars(a(:,[keys {'throughput_Mbps','spectral_efficiency','feedback_bits'}]), ...
 {'throughput_Mbps','spectral_efficiency','feedback_bits'},{'observed_Mbps','observed_SE','observed_bits'});
b=renamevars(b(:,[keys {'throughput_Mbps','spectral_efficiency','feedback_bits'}]), ...
 {'throughput_Mbps','spectral_efficiency','feedback_bits'},{'perfect_Mbps','perfect_SE','perfect_bits'});
P=innerjoin(a,b,'Keys',keys);assert(height(P)==height(a)&&all(P.observed_bits==P.perfect_bits));
P.delta_Mbps=P.perfect_Mbps-P.observed_Mbps;P.delta_SE=P.perfect_SE-P.observed_SE;
end
function write_json(path,value)
fid=fopen(path,'w');assert(fid>0);fwrite(fid,jsonencode(value),'char');fclose(fid);
end
