#!/usr/bin/env python
# Here we use the camhd module to write a single-frame AVI file, only
# downloading data from the moov atom and one frame. This AVI file can
# easily be converted to raw YUV or to PNG using ffmpeg.
#
# Timothy Crone (tjcrone@gmail.com)

import camhd

# file to work with
filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'

# write single frame to avi file
frame_number = 4976
write_frame(filename, frame_number)
