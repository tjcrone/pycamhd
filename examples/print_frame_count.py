#!/usr/bin/env python
# This script uses the pycamhd module to print the number of frames in a remote
# video file.
#
# Timothy Crone (tjcrone@gmail.com)

import sys, pycamhd

# remote file
filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'

# download moov_atom from remote file
moov_atom = pycamhd.get_moov_atom(filename)

# print number of frames in remote file
frame_count = pycamhd.get_frame_count(filename, moov_atom)
sys.stdout.write("Frame count: %i\n" % frame_count)
