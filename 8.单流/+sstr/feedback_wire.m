function out=feedback_wire(action,net,active,input,varargin)
% Exact payload bit packing. Method/mode/configuration are public, not payload.
% Every scalar integer is written MSB first; matrices use MATLAB column order.
B=numel(active);R=numel(net.reference3);
if strcmp(action,'encode')
 msg=input;method=msg.method;mode=msg.mode;
 assert(isempty(setxor(fieldnames(msg),{'protocol';'method';'mode';'space';'phase_indices'}))&&strcmp(msg.protocol,'SSTR_V2'));
 space=msg.space;phase=msg.phase_indices;wire='';
else
 wire=char(input);assert(isrow(wire)&&all(wire=='0'|wire=='1'),'sstr:Wire','Nonbinary payload');
 method=varargin{1};mode=varargin{2};space=struct;phase=[];cursor=1;
end
assert(ismember(mode,{'UE_PHASE','CPU_MODEL','DOCOMO'}));
if strcmp(method,'TYPE_I')||strcmp(method,'DOCOMO_NFLOS')
 field('beam_indices',net.index_bits,[1 B]);
elseif strcmp(method,'TYPE_II')
 field('beam_indices',net.index_bits,[2 B]);field('amp_indices',3,[1 B]);field('internal_phase_indices',2,[1 B]);
elseif strcmp(method,'POS_R3')
 if strcmp(action,'decode'),space=struct('method','POS','reference_ap_ids',net.reference3,'integer_codes',[], ...
   'coordinate_bits',[13;14;9],'quantizer_id','POS_V1_PHASE_AP1_B8');end
 if strcmp(action,'encode'),assert(isequal(space.coordinate_bits,[13;14;9]));end
 field('integer_codes',[13;14;9],[3 1]);
elseif ismember(method,{'HAQSE_R3','DFT_INDEX_R3'})
 if strcmp(method,'HAQSE_R3'),kind='HAQSE';q=14;width=14;else,kind='DFT';q=NaN;width=log2(net.M);end
 if strcmp(action,'decode'),space=struct('method',kind,'reference_ap_ids',net.reference3,'integer_codes',[],'q_frequency',q);end
 if strcmp(action,'encode'),assert(isequal(space.reference_ap_ids(:),net.reference3(:)));end
 field('integer_codes',width,[2 R]);
else,error('sstr:Method','Unknown feedback method');end
if strcmp(mode,'UE_PHASE')
 assert(~strcmp(method,'DOCOMO_NFLOS'));payloadphase();
elseif strcmp(mode,'CPU_MODEL')
 assert(ismember(method,{'POS_R3','HAQSE_R3','DFT_INDEX_R3'})&&isempty(phase));
else
 assert(strcmp(method,'DOCOMO_NFLOS'));field('beta_indices',2,[B-1 1]);field('ap_dft_index',ceil(log2(B)),[1 1]);
end
if strcmp(action,'encode')
 % Decode and compare through the strict spatial boundary; metadata is public.
 decoded=sstr.feedback_wire('decode',net,active,wire,method,mode);
 assert(isequaln(decoded.space,space)&&isequal(decoded.phase_indices(:),phase(:)),'sstr:RoundTrip','Message disagrees with public protocol');
 out=wire;
else
 assert(cursor==numel(wire)+1,'sstr:WireLength','Truncated or extra payload');
 out=struct('protocol','SSTR_V2','method',method,'mode',mode,'space',space,'phase_indices',phase);
 % Validate all spatial indices after unpacking. Docomo beta fields are separate.
 testspace=space;if strcmp(method,'DOCOMO_NFLOS'),testspace=rmfield(space,{'beta_indices','ap_dft_index'});assert(space.ap_dft_index<B);end
 sstr.decode_spatial(net,active,method,testspace);
end
 function field(name,width,shape)
  if isscalar(width),width=repmat(width,prod(shape),1);else,width=width(:);end
  if strcmp(action,'encode')
   value=space.(name);assert(isequal(size(value),shape));value=value(:);
   assert(numel(value)==numel(width)&&all(isfinite(value)&value==fix(value)&value>=0&value<2.^width));
   for ii=1:numel(value),wire=[wire dec2bin(value(ii),width(ii))];end %#ok<AGROW>
  else
   value=zeros(prod(shape),1);
   for ii=1:numel(value)
    assert(cursor+width(ii)-1<=numel(wire),'sstr:WireLength','Truncated payload');
    value(ii)=bin2dec(wire(cursor:cursor+width(ii)-1));cursor=cursor+width(ii);
   end
   space.(name)=reshape(value,shape);
  end
 end
 function payloadphase
  if strcmp(action,'encode')
   assert(numel(phase)==B-1);space.phase_payload=reshape(phase,B-1,1);
  end
  field('phase_payload',4,[B-1 1]);
  if strcmp(action,'decode'),phase=space.phase_payload;end
  space=rmfield(space,'phase_payload');
 end
end
