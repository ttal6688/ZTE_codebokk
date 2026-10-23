function audit=verify_single_stream_upa
% Focused independent checks for the UPA and continuous-POS fixes.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');
addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
[net0,sim,bank]=upa.load_inputs();p=[24.321;26.789;2.123];refs=net0.reference3;active=net0.active_order(1:8);
checks=0;maxfft=0;maxposition=0;changed=0;rng(20261023,'twister');
for N=[64 256 1024]
 net=sstr.configure_upa(net0,N);assert(net.Nside^2==N&&size(net.local,1)==3);
 assert(numel(unique(net.local(2,:)))==sqrt(N)&&numel(unique(net.local(3,:)))==sqrt(N));
 assert(net.index_bits==2*log2(4*sqrt(N))&&isequal(size(net.groups),[N 16]));checks=checks+3;
 H=randn(4,N)+1j*randn(4,N);idx=unique([0 net.M-1 net.M net.M^2-1 round(linspace(0,net.M^2-1,17))]);
 F=sstr.local_beams(net,idx,net.M);G=sstr.codebook_responses(net,H,net.M);
 err=norm(H*F-G(:,idx+1),'fro')/max(1,norm(H*F,'fro'));assert(err<1e-11);maxfft=max(maxfft,err);checks=checks+1;
 raw=zeros(2,3);
 for j=1:3
  q=net.R(:,:,refs(j))'*(net.pb(:,refs(j))-p);q=q/norm(q);raw(:,j)=-q(2:3)/2;
 end
 codes=mod(round(-raw*net.M),net.M);
 [a,da]=sstr.messages_from_estimates(net,raw,codes,active,refs,6);
 [b,db]=sstr.messages_from_estimates(net,raw,codes,active,refs,14);
 assert(isequal(a.POS.direction_message,b.POS.direction_message));
 assert(isequal(a.POS.F,b.POS.F)&&isequal(a.POS.position,b.POS.position));checks=checks+2;
 delta=norm(a.HAQSE.position-b.HAQSE.position);assert(delta>1e-6);changed=changed+1;checks=checks+1;
 err=norm(da.position_unquantized-p);assert(err<1e-10);maxposition=max(maxposition,err);checks=checks+1;
 cfg=posfb.config(net);expected=floor((p-cfg.lo)./(cfg.hi-cfg.lo).*2.^[13;14;9]);
 assert(isequal(db.coordinate_message.integer_codes,expected));
 assert(isequal(db.coordinate_message.coordinate_bits,[13;14;9]));checks=checks+2;
 msg=jsondecode(jsonencode(db.coordinate_message));msg.reference_ap_ids=reshape(msg.reference_ap_ids,1,[]);
 replay=posfb.decode(net,msg,active,cfg);assert(norm(replay.F-b.POS.F,'fro')<1e-12);checks=checks+1;
 poison=msg;poison.raw_position=p;rejected=false;
 try,posfb.decode(net,poison,active,cfg);catch,rejected=true;end
 assert(rejected);checks=checks+1;
 plane=zeros(4,numel(active)*N);u=[1;.8+.1j;.6-.2j;.9];
 for slot=1:numel(active)
  bb=active(slot);q=net.R(:,:,bb)'*(net.pb(:,bb)-p);q=q/norm(q);f=-q(2:3)/2;
  plane(:,(slot-1)*N+(1:N))=u*exp(1j*2*pi*(net.ny*f(1)+net.nz*f(2))).';
 end
 [pred,diagnostic]=sstr.space_messages(net,plane,active,refs,14);
 direct=upa.localize(net,refs,diagnostic.frequency_unquantized);
 assert(norm(direct-diagnostic.position_unquantized)<1e-12&&pred.POS.direction_bits==36);checks=checks+1;
end
% Regression against the original single-polarization UPA POS spatial chain.
sample=upa.sample_channels(net0,sim,bank,399);
[~,Y]=upa.observe(sample,'LOS_NLOS_K10',active,30);
[~,oldDiagnostic]=upa.encode_directions(net0,Y,active,refs,14);
[current,currentDiagnostic]=sstr.space_messages(net0,Y,active,refs,14);
assert(max(abs(oldDiagnostic.frequency_unquantized-currentDiagnostic.frequency_unquantized),[],'all')<1e-12);checks=checks+1;
oldPosition=upa.localize(net0,refs,oldDiagnostic.frequency_unquantized);cfg=posfb.config(net0);
[oldMessage,~]=posfb.encode(oldPosition,refs,cfg,36);oldDesign=posfb.decode(net0,oldMessage,active,cfg);
assert(isequal(oldMessage,current.POS.direction_message));checks=checks+1;
assert(norm(oldDesign.F-current.POS.F,'fro')<1e-12&&norm(oldDesign.position-current.POS.position)<1e-12);checks=checks+1;
audit=struct('status','passed','checks',checks,'UPA_shapes',[8 8;16 16;32 32], ...
 'maximum_FFT_vs_explicit_codebook_relative_error',maxfft,'maximum_continuous_ray_localization_error_m',maxposition, ...
 'frequency_precision_changes_HAQSE_but_not_POS_cases',changed,'POS_bits',[13 14 9], ...
 'POS_integer_message_replayed',true,'CPU_decoder_rejects_raw_position',true, ...
 'legacy_UPA_POS_spatial_regression',true,'new_performance_claims',false);
out=fullfile(root,'results','single_stream_UPA_POS_V1_verify');if ~exist(out,'dir'),mkdir(out);end
fid=fopen(fullfile(out,'fix_unit_audit.json'),'w');assert(fid>0);fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end
