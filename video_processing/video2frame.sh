#!/bin/bash

# video file path
videopath=$1
# frame rate reduction
downsample_scale=$2
# max no. of input frames to read
max_frames_in=$3
# output folder dir
framedir=$4

# create outdir if does not exist
if [ ! -e "$framedir" ]; then
    mkdir "$framedir"
fi

# note ffmpeg start counting input frames from 0, but ouput name starts from 1
ffmpeg -i "$videopath" \
    -vf select='not(mod(n\,'"$downsample_scale"'))*lte(n\,'"$max_frames_in"')' \
    -vsync drop \
    -start_number 0 "${framedir}/%04d.png"
