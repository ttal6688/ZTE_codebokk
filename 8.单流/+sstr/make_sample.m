function sample=make_sample(net,sim,bank,sid,KdB,model)
p=bank.positions(:,sid);scatter=sim.scatterer_positions_m.';sample.position=p;
sample.H=zeros(4,net.Nap,10);sample.Z=sample.H;K=10^(KdB/10);
for b=1:10
 ap=net.ap_elements(:,:,b);los=zeros(4,net.Nap);nlos=los;
 for u=1:4
  user=p+net.ue_offsets(:,u);r=vecnorm(ap-user);los(u,:)=exp(-1j*net.k*r)./r;
  for ell=1:6,L=vecnorm(ap-scatter(:,ell))+norm(scatter(:,ell)-user);nlos(u,:)=nlos(u,:)+bank.zeta(sid,ell)*exp(-1j*net.k*L)./L;end
 end
 if strcmp(model,'LOS'),sample.H(:,:,b)=los;else
  nlos=nlos*norm(los,'fro')/norm(nlos,'fro');sample.H(:,:,b)=sqrt(K/(K+1))*los+sqrt(1/(K+1))*nlos;
 end
 rng(bank.noise_seed(sid,b),'twister');sample.Z(:,:,b)=(randn(4,net.Nap)+1j*randn(4,net.Nap))/sqrt(2);
end
end
