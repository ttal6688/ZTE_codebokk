function metric=stream_metrics(H,W,rho)
G=H*W;A=eye(size(W,2))+rho*(G'*G);A=(A+A')/2;
error=real(diag(A\eye(size(A))));sinr=max(0,1./error-1);
s=svd(G,'econ');ratio=0;if numel(s)>1,ratio=s(2)^2/max(s(1)^2,realmin);end
L=chol(A,'lower');joint=2*sum(log2(real(diag(L))));
metric=struct('SE',sum(log2(1+sinr)),'joint_SE',joint,'SINR',sinr, ...
 'singular_values',s,'second_mode_ratio',ratio,'received_gram',G'*G);
assert(metric.SE<=joint+1e-9&&all(isfinite(sinr)));
end
