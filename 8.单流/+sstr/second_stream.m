function [c2,diagnostic]=second_stream(E,c1,rho,Q)
% Fixed first column and shared per-AP spatial beams. Design uses E only.
% Two deterministic initializations, three sweeps; no evaluation truth input.
B=numel(c1);c1=c1(:);g1=E*c1/sqrt(2*B);u=g1/max(norm(g1),realmin);
residual=E-u*(u'*E);R=(residual*residual');[U,D]=eig((R+R')/2,'vector');[s,ii]=max(real(D));
if s>1e-24*max(1,norm(E,'fro')^2),v=residual'*U(:,ii);a=exp(1j*angle(v));else,a=c1.*exp(2j*pi*(0:B-1).'/B);end
seeds={a,c1.*exp(2j*pi*(0:B-1).'/B)};best=-Inf;c2=[];
for j=1:2
 candidate=seeds{j}*conj(seeds{j}(1));
 if ~isinf(Q),idx=mod(round(angle(candidate)*2^Q/(2*pi)),2^Q);candidate=exp(2j*pi*idx/2^Q);end
 value=objective(E*candidate/sqrt(2*B));
 if value>best,best=value;c2=candidate;end
end
history=best;
if isinf(Q),L=64;else,L=2^Q;end
alphabet=exp(2j*pi*(0:L-1)/L);
for sweep=1:3
 total=E*c2/sqrt(2*B);
 for b=2:B
  old=c2(b);rest=total-E(:,b)*old/sqrt(2*B);
  candidates=[old alphabet];values=objective(rest+E(:,b)*candidates/sqrt(2*B));[value,k]=max(values);chosen=candidates(k);
  if isinf(Q)
   % Fixed-iteration golden search gives a continuous coefficient; shared public algorithm.
   center=angle(chosen);left=center-2*pi/L;right=center+2*pi/L;gold=(sqrt(5)-1)/2;
   x1=right-gold*(right-left);x2=left+gold*(right-left);
   f1=objective(rest+E(:,b)*exp(1j*x1)/sqrt(2*B));f2=objective(rest+E(:,b)*exp(1j*x2)/sqrt(2*B));
   for it=1:24
    if f1>f2,right=x2;x2=x1;f2=f1;x1=right-gold*(right-left);f1=objective(rest+E(:,b)*exp(1j*x1)/sqrt(2*B));
    else,left=x1;x1=x2;f1=f2;x2=left+gold*(right-left);f2=objective(rest+E(:,b)*exp(1j*x2)/sqrt(2*B));end
   end
   if f1>value,value=f1;chosen=exp(1j*x1);end
   if f2>value,value=f2;chosen=exp(1j*x2);end
  end
  % A fixed tolerance avoids interpreting roundoff in flat objectives as an improvement.
  if value>objective(total)+1e-10,c2(b)=chosen;total=rest+E(:,b)*chosen/sqrt(2*B);end
 end
 history(end+1)=objective(total); %#ok<AGROW>
end
assert(all(diff(history)>=-1e-9)&&abs(c2(1)-1)<1e-12&&max(abs(abs(c2)-1))<1e-12);
diagnostic=struct('objective_history',history,'sweeps',3,'initializations',2,'objective','linear-MMSE sum SE', ...
 'phase_bits',Q,'CPU_grid',64,'CPU_golden_iterations',24,'uses_truth',false);
 function value=objective(g2)
  p1=sum(abs(g1).^2);p2=sum(abs(g2).^2,1);cross=abs(g1'*g2).^2;
  determinant=1+rho*(p1+p2)+rho^2*max(0,p1*p2-cross);
  value=2*log2(determinant)-log2(1+rho*p1)-log2(1+rho*p2);
 end
end
