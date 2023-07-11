% SYNTHESISED_DATA Artficially reduce quality of video frames.

% i/o directories
inputDir = 'adobe240/frames8/GOPR9634';
outputDir = 'output/GOPR9634';
mkdir(outputDir);

nVideos = 30;
gammaGain = rand(1, nVideos) * 1.5 + 1.8;
intensityOffset = rand(1, nVideos) * 0.03 + 0.035;
intensityGain = rand(1, nVideos) * 0.1 + 0.3;
saturationGain = rand(1, nVideos) * 0.2 + 0.6;
% loop through each video dir
for vNum = 1:nVideos - 1
    vInPath = fullfile(inputDir, sprintf('%03d', vNum));
    vOutPath = fullfile(outputDir, sprintf('%03d', vNum));
    mkdir(vOutPath);
    Degrade_Frames(vOutPath, ...
                   gammaGain(vNum), ...
                   intensityOffset(vNum), ...
                   saturationGain(vNum));
end

function Degrade_Frames(frame_dir, ...
                        gamma_gain, ...
                        intensity_offset, ...
                        intensity_gain, ...
                        saturation_gain)
    imgList = dir(fullfile(frame_dir, '*.png')).name;
    for f = 1:length(imgList)
        % read clean frame
        imgHR = im2double(imread(fullfile(frame_dir, imgList(f))));
        % resize to lower resolution
        imgLR = imresize(imgHR, 0.5);
        % Gamma transform - WHY?
        imgGam = real(imgLR.^gamma_gain); % + 0.050;
        % add noise: poisson and guassian
        pNoise = sqrt(1 .* imgGam) .* normrnd(0, 0.01, size(imgGam));
        gNoise = normrnd(0, 0.05, size(imgGam));
        imgNoisy = real(imgGam + pNoise + gNoise);
        % normalise noise with the same parameter for whole video sequence
        if f == 1
            minNoise = min(imgNoisy(:));
            rangeNoise = range(imgNoisy(:));
        end
        imgNoisy = (imgNoisy - minNoise) / rangeNoise;
        % offset brightness
        imgNoisy = imgNoisy + intensity_offset;
        % dim brightness (linear)
        imgDark = intensity_gain .* imgNoisy;
        % desaturate
        hsvImg = rgb2hsv(imgDark);
        hsvImg(:, :, 2) = saturation_gain * hsvImg(:, :, 2);
        imgDark = hsv2rgb(hsvImg);
        imwrite(imgDark, fullfile(vOutPath, imgList(f)));
    end
end
