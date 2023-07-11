function Degrade_Frames(frame_dir, ...
                        output_dir, ...
                        gamma_gain, ...
                        intensity_offset, ...
                        intensity_gain, ...
                        saturation_gain)
    % DEGRADE_FRAMES Downsample, add noise and dim frames.
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
        imwrite(imgDark, fullfile(output_dir, imgList(f)));
    end
end
