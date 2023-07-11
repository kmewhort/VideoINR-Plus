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
    Degrade_Frames(vInPath, ...
                   vOutPath, ...
                   gammaGain(vNum), ...
                   intensityOffset(vNum), ...
                   saturationGain(vNum));
end
