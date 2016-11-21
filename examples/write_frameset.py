#!/usr/bin/env python
# This script downloads a single frame from every video in the archive.
#
# Timothy Crone (tjcrone@gmail.com)

import camhd

# get a list of all the files in the archive
file_list = camhd.get_file_list()

# loop through file list and write out frame 4200
j = 0
for filename in file_list:
  print filename
  j = j + 1
  try:
    camhd.write_frame(filename, 4200)
  #  write_frame(filename, 4200)
  #  j = j+1
  except:
    print "error"
    pass
  if j == 200:
    break
