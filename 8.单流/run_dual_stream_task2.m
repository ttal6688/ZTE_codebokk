function audit=run_dual_stream_task2(varargin)
% Full UPA single-polarization two-stream scan, using the verified case runner.
% Separate workers write disjoint case directories. Finalize after all finish.
root=fileparts(mfilename('fullpath'));addpath(root);maxNumCompThreads(1);
p=inputParser;addParameter(p,'OutputDir',fullfile(root,'results','dual_stream_full400'));
addParameter(p,'SampleIds',1:400);addParameter(p,'Stage','all');addParameter(p,'Worker',1);addParameter(p,'Workers',1);
parse(p,varargin{:});opt=p.Results;out=char(opt.OutputDir);settings=scan_settings();
physical=unique([[settings.Nant].' [settings.B].' [settings.SNRdB].' [settings.KdB].'],'rows','stable');
for j=1:numel(settings)
 settings(j).case_id=find(all(physical==[settings(j).Nant settings(j).B settings(j).SNRdB settings(j).KdB],2));
end
assert(ismember(opt.Stage,{'all','run','finalize'}));
if ~exist(out,'dir'),mkdir(out);end
if ~strcmp(opt.Stage,'finalize')
 for k=opt.Worker:opt.Workers:size(physical,1)
  caseDir=fullfile(out,'cases',sprintf('case_%02d',k));q=physical(k,:);
  assert(~exist(fullfile(caseDir,'audit.json'),'file'),'Existing case: use a new OutputDir');
  run_dual_stream_minimal('SampleIds',opt.SampleIds,'OutputDir',caseDir,'AntennaCount',q(1), ...
   'APCount',q(2),'ObservationSNR',q(3),'RicianK',q(4),'ChannelModels',{'LOS','MIX'});
  fprintf('FULL worker%d completed case%d/%d\n',opt.Worker,k,size(physical,1));
 end
end
audit=struct('status','worker_completed');if strcmp(opt.Stage,'run'),return;end
assert(~exist(fullfile(out,'dual_stream_summary.csv'),'file'),'Already finalized');
summaries={};pairs={};elapsed=0;
for k=1:size(physical,1)
 caseDir=fullfile(out,'cases',sprintf('case_%02d',k));a=jsondecode(fileread(fullfile(caseDir,'audit.json')));
 c=jsondecode(fileread(fullfile(caseDir,'experiment_contract.json')));
 assert(strcmp(a.status,'passed')&&isequal(c.sample_ids(:),opt.SampleIds(:)));
 assert(isequal([c.N c.B c.observation_SNR_dB c.K_dB],physical(k,:)));elapsed=elapsed+a.elapsed_seconds;
 S=readtable(fullfile(caseDir,'dual_stream_summary.csv'),'TextType','string');
 P=readtable(fullfile(caseDir,'single_dual_pairs.csv'),'TextType','string');
 for j=find([settings.case_id]==k)
  sq=S;pq=P;sq.curve=repmat(string(settings(j).curve),height(S),1);pq.curve=repmat(string(settings(j).curve),height(P),1);
  sq.x_value=repmat(settings(j).xvalue,height(S),1);pq.x_value=repmat(settings(j).xvalue,height(P),1);
  for f={'Nant','B','SNRdB','KdB'}
   sq.(f{1})=repmat(settings(j).(f{1}),height(S),1);pq.(f{1})=repmat(settings(j).(f{1}),height(P),1);
  end
  sq.case_id=repmat(k,height(S),1);pq.case_id=repmat(k,height(P),1);
  summaries{end+1}=sq;pairs{end+1}=pq; %#ok<AGROW>
 end
end
S=vertcat(summaries{:});P=vertcat(pairs{:});writetable(S,fullfile(out,'dual_stream_summary.csv'));writetable(P,fullfile(out,'single_dual_pairs.csv'));
contract=struct('version','UPA_SINGLEPOL_DUAL_FULL_V1','sample_ids',opt.SampleIds,'settings',settings, ...
 'physical_settings',physical,'channel_models',{{'LOS','MIX'}},'bandwidth_Hz',400e6,'rows_per_case',22, ...
 'shared_F',true,'algorithm','unchanged minimal implementation; same first column and per-AP second relative phase', ...
 'payload','CPU unchanged; UE adds4*(B-1) bits','power','total1, each AP1/B, each stream1/2', ...
 'evaluation','linear-MMSE sum SE; joint rate also saved; true CSI direct equal-power SVD references', ...
 'case_data','cases/case_XX/dual_stream_trials.csv.gz after packaging; repeated default scan labels reuse identical cases', ...
 'note','LOS ignores K in channel generation; LOS K scan is an intentional consistency control, not a physical K response');
write_json(fullfile(out,'experiment_contract.json'),contract);
audit=struct('status','passed','positions',numel(opt.SampleIds),'physical_settings',size(physical,1),'scan_labels',numel(settings), ...
 'physical_channel_position_cases',size(physical,1)*2*numel(opt.SampleIds),'expanded_channel_position_cases',numel(settings)*2*numel(opt.SampleIds), ...
 'physical_records',22*size(physical,1)*2*numel(opt.SampleIds),'expanded_records',22*numel(settings)*2*numel(opt.SampleIds), ...
 'expanded_pairs',height(P),'full_dual_scan',isequal(opt.SampleIds,1:400),'sum_case_elapsed_seconds',elapsed);
write_json(fullfile(out,'audit.json'),audit);disp(audit);
end
function settings=scan_settings()
settings=struct('curve',{},'xvalue',{},'Nant',{},'B',{},'SNRdB',{},'KdB',{});
for x=20:5:40,settings(end+1)=item('SNR',x,1024,8,x,10);end
for x=[64 256 1024],settings(end+1)=item('天线数',x,x,8,30,10);end
for x=5:10,settings(end+1)=item('AP数',x,1024,x,30,10);end
for x=0:5:20,settings(end+1)=item('莱斯因子',x,1024,8,30,x);end
end
function q=item(curve,x,N,B,SNR,K)
q=struct('curve',curve,'xvalue',x,'Nant',N,'B',B,'SNRdB',SNR,'KdB',K);
end
function write_json(path,value)
fid=fopen(path,'w');assert(fid>0);fwrite(fid,jsonencode(value),'char');fclose(fid);
end
