function [Htrue,Hobs]=observe_sample(sample,ids,snr)
Htrue=reshape(sample.H(:,:,ids),4,[]);Z=reshape(sample.Z(:,:,ids),4,[]);
Hobs=Htrue+sqrt(mean(abs(Htrue(:)).^2)/10^(snr/10))*Z;
end
