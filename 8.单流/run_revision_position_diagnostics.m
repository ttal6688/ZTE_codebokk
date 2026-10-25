function run_revision_position_diagnostics
% Keep the coordinate-before/after diagnostic at the new SNR points.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
out=fullfile(root,'results','upa_snr_revision400_20261025');
assert(~exist(fullfile(out,'position_diagnostics.csv'),'file'),'Diagnostics already exist');
[net0,sim,bank]=upa.load_inputs();net=sstr.configure_upa(net0,1024);active=net.active_order(1:8);
settings=[[-20:5:20 30 40].' repmat(10,11,1);repmat(30,4,1) [0;5;15;20]];
rows=cell(0,1);started=tic;
for j=1:size(settings,1)
 snr=settings(j,1);k=settings(j,2);
 for model={'LOS','MIX'}
  for sid=1:400
   sample=sstr.make_sample(net,sim,bank,sid,k,model{1});[~,obs]=sstr.observe_sample(sample,active,snr);
   [pred,d]=sstr.space_messages(net,obs,active,net.reference3,14);
   rows{end+1}=struct('channel_model',model{1},'sample_id',sid,'SNR',snr,'K',k, ...
    'raw_position_error_m',norm(d.position_unquantized-sample.position), ...
    'position_error_m',norm(pred.POS.position-sample.position), ...
    'quantizer_overflow',d.quantizer_overflow); %#ok<AGROW>
  end
 end
 fprintf('Position diagnostics SNR%g K%g: %.1f s\n',snr,k,toc(started));
end
writetable(struct2table(vertcat(rows{:})),fullfile(out,'position_diagnostics.csv'));
end
