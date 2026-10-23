function audit=verify_single_stream_protocol(outputDir)
% Algorithm-level regressions plus full integer wire boundary tests.
root=fileparts(mfilename('fullpath'));dep=fullfile(root,'6.位置反馈方案');addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
if nargin<1,outputDir=fullfile(root,'results','single_stream_UPA_V2_verify');end
if ~exist(outputDir,'dir'),mkdir(outputDir);end
legacy=verify_single_stream_upa;[net0,~,~]=upa.load_inputs();checks=0;cases=0;maxerr=0;maxorth=0;
rng(20261023,'twister');p=[24.321;26.789;2.123];
for N=[64 256 1024]
 net=sstr.configure_upa(net0,N);
 for B=[5 8 10]
  active=net.active_order(1:B);H=randn(4,N*B)+1j*randn(4,N*B);
  [one,two,detail]=sstr.baseline_messages(net,H,active);old=upa.design_baselines(net,H,H,active,4);
  % Frozen folder6 preserved original joint-mode / orthogonal-group definitions.
  assert(norm(detail.F1-old{3}.F,'fro')<1e-9&&norm(detail.F2-old{2}.F,'fro')<1e-9);checks=checks+1;
  for b=1:B
   pair=sstr.local_beams(net,two.space.beam_indices(:,b),net.M);e=abs(pair(:,1)'*pair(:,2));
   assert(e<1e-10);maxorth=max(maxorth,e);checks=checks+1;
  end
  [c,phase]=sstr.project_phases(detail.F1,detail.target,4);
  [crot,phaserot]=sstr.project_phases(detail.F1,detail.target*exp(.731j),4);
  assert(c(1)==1&&numel(phase)==B-1&&isequal(phase,phaserot)&&norm(c-crot)==0);checks=checks+1;
  % Direct global mode oracle with explicit codewords at the small array size.
  if N==64
   C=sstr.local_beams(net,0:net.M^2-1,net.M);[~,~,V]=svd(H,'econ');
   for b=1:B
    vb=V((b-1)*N+(1:N),1);g=vb'*C;[~,idx]=max(abs(g));assert(one.space.beam_indices(b)==idx-1);
    energies=sort(abs(g(net.groups)).^2,1,'descend');chosen=two.space.beam_indices(:,b)+1;
    assert(abs(sum(abs(g(chosen)).^2)-max(sum(energies(1:2,:),1)))<1e-10);checks=checks+2;
   end
  end
  raw=zeros(2,3);
  for j=1:3,q=net.R(:,:,net.reference3(j))'*(net.pb(:,net.reference3(j))-p);q=q/norm(q);raw(:,j)=-q(2:3)/2;end
  pred=sstr.messages_from_estimates(net,raw,mod(round(-raw*net.M),net.M),active,net.reference3,14);
  md=sstr.docomo_message(net,H,active);messages={one,two,md};items={pred.HAQSE,pred.DFT,pred.POS};
  for j=1:3
   item=items{j};[~,qphase]=sstr.project_phases(item.F,detail.target,4);
   m=struct('protocol','SSTR_V2','method',item.method_id,'mode','UE_PHASE','space',item.direction_message,'phase_indices',qphase);
   messages{end+1}=m;m.mode='CPU_MODEL';m.phase_indices=[];messages{end+1}=m;
  end
  for j=1:numel(messages)
   msg=messages{j};wire=sstr.feedback_wire('encode',net,active,msg);
   decoded=sstr.feedback_wire('decode',net,active,wire,msg.method,msg.mode);
   assert(isequaln(msg,decoded));checks=checks+1;
   d=sstr.decode_feedback(net,active,wire,msg.method,msg.mode);cases=cases+1;
   assert(abs(norm(d.w)^2-1)<1e-10);checks=checks+1;
   k=net.index_bits;extra=4*(B-1)*strcmp(msg.mode,'UE_PHASE');
   switch msg.method
    case 'TYPE_I',bits=B*k;case 'TYPE_II',bits=2*B*k+5*B;
    case 'DOCOMO_NFLOS',bits=B*k+2*(B-1)+ceil(log2(B));
    case 'HAQSE_R3',bits=84;case 'DFT_INDEX_R3',bits=3*k;case 'POS_R3',bits=36;
   end
   assert(numel(wire)==bits+extra);checks=checks+1;
   % Genuine CPU replay from serialized bits and public parameters only.
   again=sstr.decode_feedback(net,active,jsondecode(jsonencode(wire)),msg.method,msg.mode);
   e=norm(d.w-again.w);assert(e<1e-11);maxerr=max(maxerr,e);checks=checks+1;
   assert(rejects(@()sstr.decode_feedback(net,active,wire(1:end-1),msg.method,msg.mode)));checks=checks+1;
   assert(rejects(@()sstr.decode_feedback(net,active,[wire '0'],msg.method,msg.mode)));checks=checks+1;
   poison=msg;poison.space.raw_position=p;
   assert(rejects(@()sstr.feedback_wire('encode',net,active,poison)));checks=checks+1;
  end
 end
end
% Relative projection phase independently checked with exact on-grid phases.
F=repmat([1;0;0],1,5);v=reshape(F.*exp(1j*[.3 .3+pi/2 .3-pi .3-pi/2 .3+pi/4]),[],1);
[c,k]=sstr.project_phases(F,v,4);assert(isequal(k,[4;8;12;2])&&abs(c(1)-1)<1e-12);checks=checks+1;
audit=struct('status','passed','checks',checks,'preserved_UPA_POS_checks',legacy.checks, ...
 'UPA_shapes',[8 8;16 16;32 32],'AP_counts',[5 8 10],'wire_cases',cases, ...
 'maximum_wire_replay_precoder_error',maxerr,'maximum_TypeII_beam_inner_product',maxorth, ...
 'joint_mode_explicit_oracle',true,'legacy_spatial_baseline_regression',true, ...
 'relative_phase_global_rotation_invariant',true,'rejects_UE_raw_estimates',true, ...
 'truncated_and_extra_payloads_rejected',true);
fid=fopen(fullfile(outputDir,'protocol_unit_audit.json'),'w');assert(fid>0);fwrite(fid,jsonencode(audit),'char');fclose(fid);
fid=fopen(fullfile(outputDir,'preserved_UPA_POS_audit.json'),'w');assert(fid>0);fwrite(fid,jsonencode(legacy),'char');fclose(fid);disp(audit);
end
function yes=rejects(f)
yes=false;try,f();catch,yes=true;end
end
