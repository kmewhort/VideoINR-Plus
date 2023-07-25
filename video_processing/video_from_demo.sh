#!/bin/bash

dir=$1
subdir=(Bicubic LR VideoINR)
rate=(239.76 29.97 239.76)

for i in 0 1 2
do
    ./frame2video.sh $dir/${subdir[i]}/%d.png ${rate[i]} $dir/${subdir[i]}.mp4
done
