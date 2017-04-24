#######
PyCamHD
#######

This repository contains a Python module for interacting with data from the OOI CamHD
seafloor camera system stored in the `raw data archive`_. It can be used to obtain
information about remote CamHD files or retrieve individual frames from these files
without downloading them entirely. The code here is currently under heavy development,
so the module is changing fast and often. We are considering moving the code to a
class-paradigm, so a lot may change in the coming months. Please take this into
consideration when developing code based on this module.

We are actively recruiting anyone interested in the CamHD data to participate in the
development of this code. Join up and contribute if you have time. Pull requests
greatly appreciated!

.. _raw data archive: https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/

************
Requirements
************

This module currently only works with Python 2.7. It also requires `Requests`_ and
`this`_ fork of PyAV.

.. _Requests: https://pypi.python.org/pypi/requests
.. _this: https://github.com/markreidvfx/PyAV

************
Installation
************

::

  $ git clone https://github.com/tjcrone/pycamhd.git
  $ cd pycamhd
  $ pip install .

<!---
Or you can download pycamhd-0.6.tar.gz_ directly, unzip the file and pip install at the top level directory containing setup.py.

::

  $ tar xzvf pycamhd-0.5.tar.gz
  $ cd pycamhd-0.5
  $ pip install .

.. _pycamhd-0.5.tar.gz: https://bitbucket.org/tjcrone/pycamhd/raw/default/dist/pycamhd-0.5.tar.gz

--->

***********
Basic Usage
***********

**Write a frame to a single-frame AVI file**::

  >>> import pycamhd
  >>> filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'
  >>> moov_atom = pycamhd.get_moov_atom(filename)
  >>> frame_count = pycamhd.get_frame_count(filename, moov_atom)
  >>> print(frame_count)
  >>> frame_number = 4976 # random choice
  >>> pycamhd.write_frame(filename, frame_number, moov_atom)

The resulting AVI file can be converted to a TIFF, PNG, YUV, or another image or
movie format using ffmpeg. YUV conversions are lossless, as would be conversions to
any valid container format using a video stream copy. All CamHD ProRes encoded video
frames are key frames.

*Note: Obtaining the moov_atom first and passing it to any function is optional, but
doing so will greatly speed up repeated calls to most functions for the same file.
When multiple frames are to be obtained from the same file, getting the moov_atom
first is recommended.*

**Get information about the remote archive**::

  >>> (file_count, total_size) = pycamhd.get_stats()
  >>> print(file_count)
  >>> print(total_size)
  >>> file_list = pycamhd.get_file_list()
  >>> for filename in file_list:
  ...   print filename

*Note: Getting information about the repository can take several minutes, depending
on server response times, because every index file must be downloaded*

******************
Function Reference
******************

Archive Stats
=============

pycamhd.get_stats()
  Return the total number of MOV files and the total size of the MOV files
  (in TB) in the data archive. Returns an integer and a float.

pycamhd.get_file_list()
  Return a list of all MOV files in the data archive as fully-qualified URLs.
  Returns a list of strings.

Individual File Information
===========================

pycamhd.get_atom_sizes(filename)
  Return the sizes of the three top-level atoms in a remote file. Returns
  three integers.

pycamhd.get_chunk_count(filename[, moov_atom])
  Return the number of video chunks in a remote file. moov_atom should be a
  string containing raw packed binary data as returned by get_moov_atom().
  Returns an integer.

pycamhd.get_chunk_offsets(filename[, moov_atom])
  Return the offsets of all chunks in a remote file. Returns a list of
  integers.

pycamhd.get_frame_count(filename[, moov_atom])
  Return the number of frames in a remote file. Returns an integer.

pycamhd.get_frame_sizes(filename[, moov_atom])
  Return the sizes of all frames in a remote file. Returns a list of integers.

pycamhd.get_frame_offsets(filename[, moov_atom])
  Return the offsets of all frames in a remote file. Returns a list of
  integers.

Retrieve File Components
========================

pycamhd.get_moov_atom(filename)
  Retrieve the moov atom from a remote file. Returns a string containing raw
  packed binary data.

pycamhd.get_frame_data(filename, frame_number[, moov_atom])
  Retrieve the raw ProRes encoded frame data from a frame in a remote file.
  Returns a string containing raw packed binary data.

pycamhd.get_avi_file(frame_data)
  Adds an appropriately structured AVI header to frame_data. frame_data should
  be a string containing raw packed binary data as returned by
  get_frame_data(). Returns a string containing raw packed binary data.

Write Output File
=================

pycamhd.write_frame(filename, frame_number[, moov_atom])
  Writes a single-frame AVI file. The resulting AVI file can be converted to a
  TIFF, PNG, YUV, or another image or movie format using ffmpeg. YUV
  conversions are lossless, as would be conversions to any valid container
  format using a video stream copy. All CamHD ProRes encoded video frames are
  key frames.

Low-level Functions
===================

pycamhd.get_bytes(filename, byte_range)
  Retrieve a subset of bytes from a remote file. filename should be a fully
  qualified URL specifiying a remote CamHD Quicktime MOV file. byte_range
  should be a two-element list. Returns a string containing raw packed
  binary data.

pycamhd.get_integer(filename, byte_range)
  Return a 32-bit or 64-bit big-endian integer from a remote file.
  byte_range should be a two-element list specifying a 4-byte or 8-byte
  range.

Misc
====

pycamhd.__version__
  Print the current version number of the module.

*******
License
*******

MIT License Copyright (c) 2016 Timothy Crone

******
Author
******

Timothy Crone (tjcrone@gmail.com)
