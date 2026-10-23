function net=configure_upa(net0,N)
% Preserve public UPA deployment; change only its square spatial aperture.
side=round(sqrt(N));assert(side^2==N&&ismember(side,[8 16 32]));
net=net0;net.Nside=side;net.Nap=N;net.M=4*side;net.index_bits=2*ceil(log2(net.M));
[ny,nz]=ndgrid(0:side-1,0:side-1);net.ny=ny(:);net.nz=nz(:);
net.local=[zeros(1,N);(ny(:).'-(side-1)/2)*net.d;(nz(:).'-(side-1)/2)*net.d];
net.ap_elements=zeros(3,N,10);
for b=1:10,net.ap_elements(:,:,b)=net.pb(:,b)+net.R(:,:,b)*net.local;end
net.groups=zeros(N,16);column=0;
for oz=0:3
 for oy=0:3
  column=column+1;[my,mz]=ndgrid(oy+4*(0:side-1),oz+4*(0:side-1));
  net.groups(:,column)=my(:)+net.M*mz(:)+1;
 end
end
assert(strcmp(net.array,'UPA32x32')&&size(net.local,2)==side^2);
end
