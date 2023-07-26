#!/bin/bash

# Generate noisy, Low-Res .png frames from adobe240 dataset.

trainlist=../data/adobe240fps_folder_train.txt
testlist=../data/adobe240fps_folder_test.txt
validlist=../data/adobe240fps_folder_valid.txt
vidlist=("$trainlist" "$testlist" "$validlist")
subdir=(train test valid)

FR_scale=1 # DO NOT reduce frame rate (important for VideoINR training)
max_frames=100 # output frames 0-100

echo Start time: "$(date)"

for i in 0 1 2; do
    while IFS=$' \t\n\r' read -r vname; do
        outdir="adobe240/framesLQ_${max_frames}/${subdir[i]}/${vname}" # for LFR+noisy
        if [ ! -e "$outdir" ]; then
            echo $'\n\n'"STARTED video $vname"$'\n'
            inpath=$(find adobe240/original_videos/"$vname".*) # video input
            tmpdir=$(mktemp -d -p .)                           # for LFR

            # make LFR, save to temp
            ./video2frame.sh "$inpath" "$FR_scale" "$max_frames" "$tmpdir"

            # make noisy from temp, save to out
            echo "Exporting frames to $outdir using MATLAB..."
            scale=4 # res downscale
            matlab -batch "Degrade_Frames('$tmpdir', '$outdir', $scale, [], [], [], [])"

            rm -r "$tmpdir" # remove tmp dir

            echo $'\n'FINISHED$'\n\n'
        fi
    done <"${vidlist[i]}"
done

echo Finish time: "$(date)"
