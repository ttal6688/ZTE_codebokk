function G=codebook_responses(net,H,M)
% Exact H*C for the positive-exponent 2D DFT codebook, without storing C.
assert(size(H,2)==net.Nap);G=zeros(size(H,1),M*M);
for u=1:size(H,1)
    A=ifft2(reshape(H(u,:),net.Nside,net.Nside),M,M)*(M*M/sqrt(net.Nap));
    G(u,:)=reshape(A,1,[]);
end
end
