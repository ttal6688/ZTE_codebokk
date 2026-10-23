function [wire,diagnostic]=encode_dual(net,Hobs,active,single,rho)
% UE encodes only second-stream AP phases, retaining the original entire payload.
E=sstr.effective_channel(Hobs,single.F);[c2,diagnostic]=sstr.second_stream(E,single.c,rho,4);
indices=mod(round(angle(c2(2:end))*16/(2*pi)),16);wire=single.feedback_wire;
for b=1:numel(indices),wire=[wire dec2bin(indices(b),4)];end %#ok<AGROW>
expected=zeros(net.Nap*numel(active),2);C=[single.c c2]/sqrt(2*numel(active));
for b=1:numel(active),expected((b-1)*net.Nap+(1:net.Nap),:)=single.F(:,b)*C(b,:);end
d=sstr.decode_dual(net,active,wire,single.method_id,single.feedback_message.mode,rho);
assert(norm(d.W-expected,'fro')<1e-11);
end
