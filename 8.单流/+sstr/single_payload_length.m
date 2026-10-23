function n=single_payload_length(net,B,method,mode)
switch method
 case 'TYPE_I',n=B*net.index_bits;
 case 'TYPE_II',n=2*B*net.index_bits+5*B;
 case 'DOCOMO_NFLOS',n=B*net.index_bits+2*(B-1)+ceil(log2(B));
 case 'HAQSE_R3',n=84;
 case 'DFT_INDEX_R3',n=3*net.index_bits;
 case 'POS_R3',n=36;
 otherwise,error('sstr:Method','Unknown method');
end
if strcmp(mode,'UE_PHASE'),n=n+4*(B-1);end
end
