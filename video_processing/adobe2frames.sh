#!/bin/bash

# Generate ground-truth or low-quality .png frames from adobe240 dataset.

mode=$1

if [ "$mode" = '' ]; then
    echo Must give mode \'LQ\' or \'GT\'
    exit 42
fi

trainlist=../data/adobe240fps_folder_train.txt
testlist=../data/adobe240fps_folder_test.txt
validlist=../data/adobe240fps_folder_valid.txt
vidlist=("$trainlist" "$testlist" "$validlist")
subdir=(train test valid)

FR_scale=1     # DO NOT reduce frame rate (important for VideoINR training)
max_frames=100 # output frames 0-100

echo Start time: "$(date)"

for i in 0 1 2; do
    while IFS=$' \t\n\r' read -r vname; do
        outdir="adobe240/frames${mode}_${max_frames}/${subdir[i]}/${vname}"
        if [ ! -e "$outdir" ]; then
            # for low-qualilty
            echo $'\n\n'"STARTED video $vname"$'\n'
            inpath=$(find adobe240/original_videos/"$vname".*) # video input

            if [ "$mode" = LQ ]; then
                tmpdir=$(mktemp -d -p .) # for LFR

                # make LFR, save to temp
                ./video2frame.sh "$inpath" "$FR_scale" "$max_frames" "$tmpdir"

                # make noisy from temp, save to out
                echo "Exporting frames to $outdir using MATLAB..."
                scale=4 # res downscale
                matlab -batch "Degrade_Frames('$tmpdir', '$outdir', $scale, [], [], [], [])"

                rm -r "$tmpdir" # remove tmp dir

            elif [ "$mode" = GT ]; then
                # for ground truth
                mkdir -p "$outdir"
                ./video2frame.sh "$inpath" "$FR_scale" "$max_frames" "$outdir"
            else
                echo 'Error: Invalid export mode! Must be' \'LQ\' 'or' \'GT\'
                exit 69
            fi

            echo $'\n'FINISHED$'\n\n'
        fi
    done <"${vidlist[i]}"
done

echo Finish time: "$(date)"
