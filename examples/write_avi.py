#!/usr/bin/env python
# This script uses the camhd module to write a single-frame AVI file, only
# downloading data from the moov atom and one frame. This AVI file can be
# converted to a PNG or losslessly to a raw YUV using ffmpeg.
#
# Timothy Crone (tjcrone@gmail.com)

import camhd

# remote file
filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'

# write single frame to avi file
frame_number = 4976
camhd.write_frame(filename, frame_number)
