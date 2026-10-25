function run_snr_revision400(varargin)
% Additional paired single/two-stream cases. Existing high-SNR data are reused.
root=fileparts(mfilename('fullpath'));addpath(root);maxNumCompThreads(1);
p=inputParser;addParameter(p,'Worker',1);addParameter(p,'Workers',1);
addParameter(p,'SampleIds',1:400);addParameter(p,'OutputDir',fullfile(root,'results','upa_snr_revision400_20261025'));
parse(p,varargin{:});o=p.Results;snrs=-20:5:15;
for k=o.Worker:o.Workers:numel(snrs)
 out=fullfile(o.OutputDir,'cases',sprintf('snr_%+03d',snrs(k)));
 if exist(fullfile(out,'audit.json'),'file')
  a=jsondecode(fileread(fullfile(out,'audit.json')));
  assert(strcmp(a.status,'passed')&&isequal(a.sample_ids(:),o.SampleIds(:)));continue;
 end
 run_dual_stream_minimal('SampleIds',o.SampleIds,'OutputDir',out,'AntennaCount',1024, ...
  'APCount',8,'ObservationSNR',snrs(k),'RicianK',10,'ChannelModels',{'LOS','MIX'});
end
end
