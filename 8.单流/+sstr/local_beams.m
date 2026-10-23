function F=local_beams(net,index,M)
% Zero-based linear index: y is fast, z is slow.
index=reshape(index,1,[]);my=mod(index,M);mz=floor(index/M);
assert(all(index==round(index)&index>=0&index<M*M));
F=exp(1j*2*pi*(net.ny*my+net.nz*mz)/M)/sqrt(net.Nap);
end
