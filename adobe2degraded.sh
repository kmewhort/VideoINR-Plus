#!/bin/bash

# Generate Low-Frame-Rate, noisy, Low-Res .png frames from adobe240 dataset.

trainlist=data/adobe240fps_folder_train.txt
testlist=data/adobe240fps_folder_test.txt
validlist=data/adobe240fps_folder_valid.txt
vidlist=("$trainlist" "$testlist" "$validlist")
subdir=(train test valid)

FR_scale=8
max_frames_in=800 # gives 100 frames output

echo Start time: "$(date)"

for i in 0 1 2; do
    while IFS=$' \t\n\r' read -r vname; do
        outdir="adobe240/framesLQ_800/${subdir[i]}/$vname" # for LFR+noisy
        if [ ! -e "$outdir" ]; then
            inpath=$(find adobe240/original_videos/"$vname".*) # video input
            tmpdir=$(mktemp -d -p .)                           # for LFR

            # make LFR, save to temp
            ./video2frame.sh "$inpath" "$FR_scale" "$max_frames_in" "$tmpdir"

            # make noisy from temp, save to out
            scale=4 # res downscale
            matlab -batch "Degrade_Frames('$tmpdir', '$outdir', $scale, [], [], [], [])"

            rm -r "$tmpdir" # remove tmp dir
        fi
    done <"${vidlist[i]}"
done

echo Finish time: "$(date)"
