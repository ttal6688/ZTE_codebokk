function [c,indices]=project_phases(F,v,Q)
% One common rule: project each AP beam onto the joint principal mode.
N=size(F,1);B=size(F,2);a=zeros(B,1);
for b=1:B,a(b)=F(:,b)'*v((b-1)*N+(1:N));end
theta=angle(a)-angle(a(1));
if isinf(Q),indices=[];c=exp(1j*theta);else
 indices=mod(round(theta(2:end)*2^Q/(2*pi)),2^Q);
 c=exp(1j*2*pi*[0;indices(:)]/2^Q);
end
end
