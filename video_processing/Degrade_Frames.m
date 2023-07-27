function Degrade_Frames(frame_indir, ...
                        frame_outdir, ...
                        scale, ...
                        gamma, ...
                        intensity_offset, ...
                        intensity_gain, ...
                        saturation)
% DEGRADE_FRAMES Downsample, add noise and dim frames.
%   Original code: Dr Pui Anantrasirichai, 2023 (University of Bristol)
%   Adapted: Felix Dubicki-Piper, 2023 (UG, University of Bristol)
%
%   Recommended Default Input Values:
%       gammaGain       = 1.8   + rand() * 1.5
%       intensityOffset = 0.035 + rand() * 0.03;
%       intensityGain   = 0.3   + rand() * 0.1;
%       saturationGain  = 0.6   + rand() * 0.2;


mkdir(frame_outdir);
imgList = {dir(fullfile(frame_indir, '*.png')).name};
for f = 1:length(imgList)
    % read clean frame
    img = im2double(imread(fullfile(frame_indir, imgList{f})));

    % gamma transform - mimicks lowering camera aperture
    if ~isequal(gamma, [])
        img = real(img.^gamma); % + 0.050;
    end

    % add noise: poisson and guassian
    % - poisson mimicks 'natural' noise
    % - gaussian is more 'artificial'
    pNoise = sqrt(1 .* img) .* normrnd(0, 0.01, size(img));
    gNoise = normrnd(0, 0.05, size(img));
    img = real(img + pNoise + gNoise);

    % normalise noise with the same parameter for whole video sequence
    if f == 1
        minNoise = min(img(:));
        rangeNoise = range(img(:));
    end
    img = (img - minNoise) / rangeNoise;

    % offset brightness - clips white point
    % - mimicks data loss ie overexposure
    if ~isequal(intensity_offset, [])
        img = img + intensity_offset;
    end

    % dim brightness (linear)
    if ~isequal(intensity_gain, [])
        img = intensity_gain .* img;
    end

    % desaturate
    if ~isequal(saturation, [])
        hsvImg = rgb2hsv(img);
        hsvImg(:, :, 2) = saturation * hsvImg(:, :, 2);
        % convert back to rgb
        img = hsv2rgb(hsvImg);
    end

    % downsample to lower resolution (scales by length, not area)
    if ~isequal(scale, [])
        img = imresize(img, 1 / scale);
    end

    imwrite(img, fullfile(frame_outdir, imgList{f}));
end
end
