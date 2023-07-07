#!/bin.bash

video_indir=$1
downsample_scale=$2
# specify only parent dir, not file pattern itself
frame_outdir=$3

# create outdir if does not exist
if [ ! -e $frame_outdir ]
then
    mkdir $frame_outdir
fi

ffmpeg -i $video_indir -vf select='not(mod(n\,'$downsample_scale'))' -vsync vfr "${frame_outdir}%d.png"
