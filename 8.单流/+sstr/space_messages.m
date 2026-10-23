function [pred,diagnostic]=space_messages(net,Hobs,active,refs,qfrequency)
raw=zeros(2,numel(refs));codes=raw;
for j=1:numel(refs)
    slot=find(active==refs(j));assert(isscalar(slot));ix=(slot-1)*net.Nap+(1:net.Nap);
    Hb=Hobs(:,ix);[~,~,v]=upa.principal(Hb);codes(:,j)=upa.spectrum(net,v);
    f=MMV_CF_mQSE2_SumOfRatios(reshape(Hb.',[net.Nside net.Nside 4]),1,1,1,3);
    raw(:,j)=mod(f(1,:).'+.5,1)-.5;
end
[pred,diagnostic]=sstr.messages_from_estimates(net,raw,codes,active,refs,qfrequency);
end
