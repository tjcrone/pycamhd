CAMHD
=====

This repository contains a Python module for interacting with data from the OOI
CamHD seafloor camera system stored in the raw data archive. It can be used to
obtain information about these remote files or retrieve individual frames
without downloading entire video files. The code here is currently under heavy
development, so the module is changing fast and often. We are considering moving
the code to a class-paradigm, so a lot may change in the coming months. Please
take this into consideration when developing code based on this module.

We are actively recruiting anyone interested in the CamHD data to participate in
the development of this code. Join up and contribute if you have time. Pull
requests greatly appreciated!

Installation
------------

::

  $ hg clone https://bitbucket.org/tjcrone/camhd
  $ pip install camhd/dist/camhd-0.4.tar.gz

Basic Usage
-----------

**Write a frame to a single-frame AVI file**::

  >>> import camhd
  >>> filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'
  >>> moov_atom = camhd.get_moov_atom(filename)
  >>> frame_count = camhd.get_frame_count(filename, moov_atom)
  >>> print(frame_count)
  >>> frame_number = 4976
  >>> camhd.write_frame(filename, frame_number, moov_atom)

The resulting AVI file can be converted to a TIFF, PNG, YUV, or other image or movie
format using ffmpeg. YUV conversions are lossless.

*Note: Obtaining the moov_atom first and passing it to any function is optional, but
it will greatly speed up calls to most functions. When multiple frames are to be
obtained from the same file, getting the moov_atom first is recommended.*

**Get information about the repository**::

  >>> (file_count, total_size) = camhd.get_stats()
  >>> print(file_count)
  >>> print(total_size)
  >>> file_list = camhd.get_file_list()
  >>> for filename in file_list:
  ...   print filename

*Note: Getting information about the repository can take several minutes, depending
on server response times, because every index file must be downloaded*

License
-------

MIT License Copyright (c) 2016 Timothy Crone

Author
------

Timothy Crone (tjcrone@gmail.com)
