#!/bin/bash

# set frame input directory
frame_indir=$1
# set frame rate
rate=$2
# set video out directory
video_outdir=$3

# convert to video
ffmpeg -framerate $rate -i $frame_indir -pix_fmt yuv420p $video_outdir
