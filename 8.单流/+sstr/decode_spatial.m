function d=decode_spatial(net,active,method,space)
% Strict spatial decoder. Inputs contain only public configuration and indices.
B=numel(active);d=struct('F',[],'position',nan(3,1),'condition',NaN,'coordinate_bits',nan(3,1));
if ismember(method,{'TYPE_I','TYPE_II','DOCOMO_NFLOS'})
 if strcmp(method,'TYPE_II'),allowed={'beam_indices','amp_indices','internal_phase_indices'};count=2;
 else,allowed={'beam_indices'};count=1;end
 assert(isempty(setxor(fieldnames(space),allowed(:))),'sstr:SpatialFields','Unexpected spatial field');
 k=reshape(space.beam_indices,count,B);assert(all(k(:)==fix(k(:))&k(:)>=0&k(:)<net.M^2));
 d.F=zeros(net.Nap,B);
 for b=1:B
  pair=sstr.local_beams(net,k(:,b),net.M);
  if count==2
   a=space.amp_indices(b);p=space.internal_phase_indices(b);
   assert(a==fix(a)&&a>=0&&a<=7&&p==fix(p)&&p>=0&&p<4);
   % Membership in the same orthogonal group is a protocol invariant.
   assert(k(1,b)~=k(2,b)&&mod(mod(k(1,b),net.M),4)==mod(mod(k(2,b),net.M),4));
   assert(mod(floor(k(1,b)/net.M),4)==mod(floor(k(2,b)/net.M),4));
   f=pair*[1;a/7*exp(1j*2*pi*p/4)];d.F(:,b)=f/norm(f);
  else,d.F(:,b)=pair;end
 end
elseif strcmp(method,'POS_R3')
 p=posfb.decode(net,space,active,posfb.config(net));d.F=p.F;d.position=p.position;d.coordinate_bits=space.coordinate_bits;
elseif ismember(method,{'HAQSE_R3','DFT_INDEX_R3'})
 p=upa.predict_directions(net,space,active);d.F=p.F;d.position=p.position;d.condition=p.localization.condition;
else,error('sstr:Method','Unknown spatial method');end
end
