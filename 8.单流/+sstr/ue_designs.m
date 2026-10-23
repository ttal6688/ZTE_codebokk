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
