#!/usr/bin/env python
# Here we use the camhd module to print the number of frames in a remote
# video file.
#
# Timothy Crone (tjcrone@gmail.com)

import camhd

# file to work with
filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'

# download moov_atom
moov_atom = camhd.get_moov_atom(filename)

# get frame count
frame_count = camhd.get_frame_count(filename, moov_atom)
print "Frame count: " + str(frame_count)
