function [one,two,detail]=baseline_messages(net,H,active)
% Project the JOINT right singular mode; Type-II searches orthogonal groups.
B=numel(active);[~,~,v]=upa.principal(H);F1=zeros(net.Nap,B);F2=F1;
i1=zeros(1,B);i2=zeros(2,B);amp=zeros(1,B);phase=amp;
for b=1:B
 vb=v((b-1)*net.Nap+(1:net.Nap));
 g=sstr.codebook_responses(net,vb',net.M); % g = v_b^H C
 [~,i1(b)]=max(abs(g));i1(b)=i1(b)-1;
 F1(:,b)=sstr.local_beams(net,i1(b),net.M);
 gp=g(net.groups);[energy,order]=sort(abs(gp).^2,1,'descend');
 [~,group]=max(sum(energy(1:2,:),1));chosen=net.groups(order(1:2,group),group);
 i2(:,b)=chosen-1;values=g(chosen);
 amp(b)=round(7*min(1,abs(values(2))/max(abs(values(1)),realmin)));
 % values are v_b^H f: the relative coefficient has the opposite phase.
 phase(b)=mod(round((angle(values(1))-angle(values(2)))*4/(2*pi)),4);
 pair=sstr.local_beams(net,i2(:,b),net.M);
 f=pair*[1;amp(b)/7*exp(1j*2*pi*phase(b)/4)];F2(:,b)=f/norm(f);
end
[~,q1]=sstr.project_phases(F1,v,4);[~,q2]=sstr.project_phases(F2,v,4);
one=struct('protocol','SSTR_V2','method','TYPE_I','mode','UE_PHASE', ...
 'space',struct('beam_indices',i1),'phase_indices',q1);
two=one;two.method='TYPE_II';two.space=struct('beam_indices',i2, ...
 'amp_indices',amp,'internal_phase_indices',phase);two.phase_indices=q2;
detail=struct('F1',F1,'F2',F2,'target',v);
end
