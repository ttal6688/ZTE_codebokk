function audit=run_reference_ap_full400(varargin)
% Formal localization supplement, separate from the cooperation-AP experiments.
root=fileparts(mfilename('fullpath'));addpath(root);
p=inputParser;addParameter(p,'OutputDir',fullfile(root,'results','reference_ap_full400_20261025'));parse(p,varargin{:});
audit=run_reference_ap_pilot('SampleIds',1:400,'OutputDir',p.Results.OutputDir);
end
