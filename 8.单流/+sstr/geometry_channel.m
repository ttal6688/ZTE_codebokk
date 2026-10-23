function H=geometry_channel(net,p,active)
% Public geometry only. No observed or simulation-truth channel input.
H=zeros(4,numel(active)*net.Nap);
for slot=1:numel(active)
 b=active(slot);delta=net.pb(:,b)-p;r=norm(delta);assert(r>0);
 q=delta/r;ql=net.R(:,:,b)'*q;ix=(slot-1)*net.Nap+(1:net.Nap);
 H(:,ix)=exp(-1j*net.k*r)/r*exp(1j*net.k*net.ue_offsets.'*q)*exp(-1j*net.k*ql.'*net.local);
end
end
