function E=effective_channel(H,F)
N=size(F,1);B=size(F,2);assert(size(H,2)==N*B);E=zeros(size(H,1),B);
for b=1:B,E(:,b)=H(:,(b-1)*N+(1:N))*F(:,b);end
end
