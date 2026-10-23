function cfg=position_config(net)
% Cache only frozen PUBLIC geometry; identical to posfb.config(net).
persistent key value
current={net.array,net.pb,net.active_order};
if isempty(key)||~isequal(key,current),value=posfb.config(net);key=current;end
cfg=value;
end
