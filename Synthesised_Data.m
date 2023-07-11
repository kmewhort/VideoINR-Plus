clear all

TrainOginRoot = 'U:\Creative\dataset_REDS\groundtruth\val_sharp';
OutputRoot = 'U:\Creative\dataset_REDS\Synthetic_LowLightLowResolution\REDS\val';
mkdir(OutputRoot);

totalSeq = 30;
intensityGain = rand(1, totalSeq)*0.1 + 0.3;
intensityOffset = rand(1, totalSeq)*0.03 + 0.035;
gammaGain = rand(1, totalSeq)*1.5 + 1.8;
saturationGain = rand(1, totalSeq)*0.2 + 0.6;
for subroot = 1:totalSeq-1
    subRootName = fullfile(TrainOginRoot, sprintf('%03d',subroot));
    subOutRood = fullfile(OutputRoot, sprintf('%03d',subroot));
    mkdir(subOutRood);
    imgList = dir(fullfile(subRootName, '*.png'));
    % read clean image
    for f = 1:length(imgList)
        imgHR = im2double(imread(fullfile(imgList(f).folder, imgList(f).name)));
        % resize to lower resolution
        imgHR = imresize(imgHR, 0.5);
        synDark =  real(imgHR.^gammaGain(subroot+1));% + 0.050;
        % adding noise: poisson and guassian
        a = 1; b = 0.05;
        noisy = real(synDark + (sqrt(a .* synDark) .* normrnd(0,0.01, size(synDark))) + normrnd(0,b, size(synDark)));
        if f == 1
            minnoise = min(noisy(:));
            rangenoise = range(noisy(:));
        end
        % normalise with the same parameter for the whole sequence
        noisy = (noisy - minnoise)/rangenoise;
        noisy = noisy + intensityOffset(subroot+1);
        % dim brightness
        synDark = intensityGain(subroot+1).*noisy;
        % dim saturation
        hsvimg = rgb2hsv(synDark);
        hsvimg(:,:,2) = saturationGain(subroot+1)*hsvimg(:,:,2);
        synDark = hsv2rgb(hsvimg);
        imwrite(synDark, fullfile(subOutRood, imgList(f).name));
    end
end