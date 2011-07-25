#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os

home_dir = os.environ['HOME']
videotop_dir = os.path.join(home_dir, '.videotop')
video_dir = os.path.join(home_dir, '.videotop/videos')
videoinfo_dir = os.path.join(home_dir, '.videotop/videoinfo')

try:
    os.mkdir(videotop_dir)
except OSError, e:
    print(e)
try:
    os.mkdir(video_dir)
except OSError, e:
    print(e)
try:
    os.mkdir(videoinfo_dir)
except OSError, e:
    print(e)
