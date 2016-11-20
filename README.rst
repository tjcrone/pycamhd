CAMHD
=====

This repository contains a Python module for interacting with data from the OOI
CamHD seafloor camera system stored in the raw data archive. It can be used to
obtain information about these files or obtain individual frames without
downloading entire video files. The code here is currently under heavy
development, so the module is changing fast and often. Almost everything about
how this module works is subject to change.

Installation
------------

To clone this repository:

.. code-block:: bash

  $ hg clone https://bitbucket.org/tjcrone/camhd

To install module using pip:

.. code-block:: bash

  $ pip install https://bitbucket.org/tjcrone/camhd/dist/camhd-0.1.tar.gz

Example usage
-------------

.. code-block:: python

  >>> import camhd
  >>> filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'
  >>> frame_number = 4976
  >>> camhd.write_frame(filename, frame_number)

License
-------

MIT License Copyright (c) 2016 Timothy Crone

Author
------

Timothy Crone (tjcrone@gmail.com)
