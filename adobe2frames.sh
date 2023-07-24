#!/bin/bash

# Generate original .png frames from adobe240 dataset.

trainlist=data/adobe240fps_folder_train.txt
testlist=data/adobe240fps_folder_test.txt
validlist=data/adobe240fps_folder_valid.txt
vidlist=("$trainlist" "$testlist" "$validlist")
subdir=(train test valid)

FR_scale=1        # don't downsample framerate
max_frames_in=800 # 800 frame output

echo Start time: "$(date)"

for i in 0 1 2; do
    while IFS=$' \t\n\r' read -r vname; do
        outdir="adobe240/framesGT_800/${subdir[i]}/$vname" # frame output
        if [ ! -e "$outdir" ]; then
            inpath=$(find adobe240/original_videos/"$vname".*) # video input
            mkdir -p "$outdir"

            # save frames
            ./video2frame.sh "$inpath" "$FR_scale" "$max_frames_in" "$outdir"
        fi
    done <"${vidlist[i]}"
done

echo Finish time: "$(date)"
