function d=decode_dual(net,active,wire,method,mode,rho)
% CPU sees only the public configuration and full payload. Stream count fixed at2.
B=numel(active);n=sstr.single_payload_length(net,B,method,mode);assert(numel(wire)>=n);
single=sstr.decode_feedback(net,active,wire(1:n),method,mode);
if strcmp(mode,'CPU_MODEL')
 assert(numel(wire)==n);H=sstr.geometry_channel(net,single.estimated_position,active);
 E=sstr.effective_channel(H,single.F);[c2,diagnostic]=sstr.second_stream(E,single.c,rho,Inf);indices=[];
else
 assert(numel(wire)==n+4*(B-1)&&all(wire=='0'|wire=='1'));indices=zeros(B-1,1);
 for b=1:B-1,indices(b)=bin2dec(wire(n+(b-1)*4+(1:4)));end
 c2=exp(2j*pi*[0;indices]/16);diagnostic=struct;
end
C=[single.c c2]/sqrt(2*B);W=zeros(net.Nap*B,2);
for b=1:B,W((b-1)*net.Nap+(1:net.Nap),:)=single.F(:,b)*C(b,:);end
d=struct('F',single.F,'C',C,'W',W,'single',single,'feedback_wire',wire,'feedback_bits',numel(wire), ...
 'second_phase_indices',indices,'diagnostic',diagnostic);
assert(abs(norm(W,'fro')^2-1)<1e-10);
for b=1:B,assert(abs(norm(W((b-1)*net.Nap+(1:net.Nap),:),'fro')^2-1/B)<1e-10);end
end
