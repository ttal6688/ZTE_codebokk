function audit=run_reference_ap_pilot(varargin)
% Hold B=8 and the complete observation fixed; vary only localization references.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');
addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
p=inputParser;addParameter(p,'OutputDir',fullfile(root,'results','reference_ap_pilot32_20261025'));
addParameter(p,'SampleIds',round(linspace(1,400,32)),@(x)isvector(x)&&all(isfinite(x)&x==fix(x)&x>=1&x<=400)&&numel(unique(x))==numel(x));
parse(p,varargin{:});out=char(p.Results.OutputDir);ids=p.Results.SampleIds(:).';
assert(~exist(fullfile(out,'localization_trials.csv'),'file')&&~exist(fullfile(out,'localization_trials.csv.gz'),'file'),'Use a new output directory');
if ~exist(out,'dir'),mkdir(out);end
[net0,sim,bank]=upa.load_inputs();net=sstr.configure_upa(net0,1024);active=net.active_order(1:8);cfg=sstr.position_config(net);
assert(isequal(active(1:3),net.reference3)&&isequal(cfg.main_allocation,[13;14;9]));
rows={};estimates={};started=tic;
for model={'LOS','MIX'}
 for sid=ids
  sample=sstr.make_sample(net,sim,bank,sid,10,model{1});[Htrue,Hobs]=sstr.observe_sample(sample,active,30);
  noisevar=mean(abs(Htrue(:)).^2)/10^3;
  % Estimate all eight APs once; every nested R uses exactly the same samples.
  [allPred,allDiag]=sstr.space_messages(net,Hobs,active,active,14);
  frequency=allDiag.frequency_unquantized;dft=allPred.DFT.direction_message.integer_codes;
  for j=1:8
   ix=(j-1)*net.Nap+(1:net.Nap);
   estimates{end+1}=struct('channel_model',model{1},'sample_id',sid,'physical_AP_id',active(j), ...
    'frequency_y',frequency(1,j),'frequency_z',frequency(2,j),'DFT_y',dft(1,j),'DFT_z',dft(2,j), ...
    'observation_noise_variance',noisevar,'true_AP_mean_power',mean(abs(Htrue(:,ix)).^2,'all')); %#ok<AGROW>
  end
  for R=3:8
   refs=active(1:R);[pred,diag]=sstr.messages_from_estimates(net,frequency(:,1:R),dft(:,1:R),active,refs,14);
   for method={'HAQSE','DFT_INDEX','POS'}
    key=method{1};if strcmp(key,'DFT_INDEX'),source=pred.DFT;else,source=pred.(key);end
    wire=pack(key,source.direction_message);
    recovered=decode(net,active,refs,key,wire,cfg);
    assert(norm(source.position-recovered.position)<1e-10&&numel(wire)==source.feedback_bits);
    position=recovered.position;
    if strcmp(key,'POS'),raw=diag.position_unquantized;condition=diag.position_localization.condition;overflow=diag.quantizer_overflow;
    else,raw=position;condition=recovered.localization.condition;overflow=false;end
    rows{end+1}=struct('channel_model',model{1},'sample_id',sid,'method',key,'B',8,'R',R,'antenna_count',1024, ...
     'observation_SNR_dB',30,'K_dB',10,'reference_AP_ids',jsonencode(refs),'feedback_wire',wire, ...
     'spatial_feedback_bits',numel(wire),'true_x_m',sample.position(1),'true_y_m',sample.position(2),'true_z_m',sample.position(3), ...
     'estimated_x_m',position(1),'estimated_y_m',position(2),'estimated_z_m',position(3), ...
     'raw_x_m',raw(1),'raw_y_m',raw(2),'raw_z_m',raw(3), ...
     'position_error_m',norm(position-sample.position),'raw_position_error_m',norm(raw-sample.position), ...
     'localization_condition',condition,'quantizer_overflow',overflow,'observation_noise_variance',noisevar); %#ok<AGROW>
   end
  end
 end
 fprintf('REFERENCE AP pilot completed %s, %.1f s\n',model{1},toc(started));
end
T=struct2table(vertcat(rows{:}));E=struct2table(vertcat(estimates{:}));
writetable(T,fullfile(out,'localization_trials.csv'));writetable(E,fullfile(out,'ap_estimates.csv'));
[g,S]=findgroups(T(:,{'channel_model','method','B','R','observation_SNR_dB','K_dB'}));S.samples=splitapply(@numel,T.sample_id,g);
for field={'position_error_m','raw_position_error_m','spatial_feedback_bits','localization_condition','quantizer_overflow'}
 S.(['mean_' field{1}])=splitapply(@mean,double(T.(field{1})),g);
end
S.median_position_error_m=splitapply(@median,T.position_error_m,g);
S.p95_position_error_m=splitapply(@(v)prctile(v,95),T.position_error_m,g);
writetable(S,fullfile(out,'localization_summary.csv'));
contract=struct('version','LOC_REF_SWEEP_V1','scope',sprintf('localization-only %d-position scan; no communication protocol extension',numel(ids)), ...
 'sample_ids',ids,'sample_selection','explicit SampleIds; default is round(linspace(1,400,32)); full scan is1:400', ...
 'B',8,'R',3:8,'Nant',1024,'observation_SNR_dB',30,'K_dB',10,'channels',{{'LOS','MIX'}}, ...
 'active_AP_ids',active,'reference_sets','first R of the public active AP order; nested and fixed before results', ...
 'noise','Hobs generated once per position and model using all eight APs; reused exactly across R', ...
 'CPU_UE','same spatial-message localization frontend; rows are shared, not duplicated independent trials', ...
 'position_feedback','continuous frequencies -> UE position -> one coordinate quantization, fixed13/14/9 bits', ...
 'payload','directions28R or14R bits; coordinates36 bits; R/method/AP order public, no phase fields in this localization-only experiment', ...
 'communication_boundary','existing SSTR_V2 full precoder decoder remains R=3; this pilot packs and decodes localization messages only', ...
 'elapsed_seconds',toc(started));write_json(fullfile(out,'experiment_contract.json'),contract);
audit=struct('status','passed','positions',numel(ids),'records',height(T),'AP_estimate_records',height(E), ...
 'all_samples_retained',true,'B_fixed',8,'R_values',3:8,'integer_localization_payload_recovered',true);
write_json(fullfile(out,'audit.json'),audit);disp(audit);
end

function wire=pack(method,message)
codes=message.integer_codes(:);
if strcmp(method,'POS'),widths=[13;14;9];elseif strcmp(method,'HAQSE'),widths=repmat(14,numel(codes),1);else,widths=repmat(7,numel(codes),1);end
wire='';for j=1:numel(codes),wire=[wire dec2bin(codes(j),widths(j))];end %#ok<AGROW>
end

function d=decode(net,active,refs,method,wire,cfg)
R=numel(refs);if strcmp(method,'POS'),widths=[13;14;9];elseif strcmp(method,'HAQSE'),widths=repmat(14,2*R,1);else,widths=repmat(7,2*R,1);end
cursor=1;codes=zeros(numel(widths),1);
for j=1:numel(widths),codes(j)=bin2dec(wire(cursor:cursor+widths(j)-1));cursor=cursor+widths(j);end
assert(cursor==numel(wire)+1);
if strcmp(method,'POS')
 message=struct('method','POS','reference_ap_ids',refs,'integer_codes',codes,'coordinate_bits',[13;14;9],'quantizer_id',cfg.id);
 d=posfb.decode(net,message,active,cfg);
else
 if strcmp(method,'HAQSE'),kind='HAQSE';q=14;else,kind='DFT';q=NaN;end
 message=struct('method',kind,'reference_ap_ids',refs,'integer_codes',reshape(codes,2,R),'q_frequency',q);
 d=upa.predict_directions(net,message,active);
end
end

function write_json(path,value)
fid=fopen(path,'w','n','UTF-8');fprintf(fid,'%s',jsonencode(value));fclose(fid);
end
