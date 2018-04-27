#!/usr/bin/env python
# This is a Python module for interacting with data from the OOI CamHD
# seafloor camera system stored in the raw data archive. It can be used to
# obtain information about these files or obtain individual frames without
# downloading entire video files. The module can also work with video files
# stored on the local filesystem.
#
# Timothy Crone (tjcrone@gmail.com)

# imports
import subprocess, struct, sys, requests, av
from datetime import date, timedelta
import numpy as np

# get arbitrary bytes from remote or local file
def get_bytes(filename, byte_range):
  if "https://" in filename:
    cmd = ('curl --header "Range: bytes=%i-%i" -k -s ' %
      (byte_range[0], byte_range[1])) + filename
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    file_bytes = p.communicate()[0]
  else:
    with open(filename, 'rb') as f:
      f.seek(byte_range[0], 0)
      file_bytes = f.read(byte_range[1] - byte_range[0] + 1)
  return file_bytes

# get big-endian 32-bit or 64-bit integer from file
def get_integer(filename, byte_range):
  file_bytes = get_bytes(filename, byte_range)
  if len(file_bytes) == 4:
    return struct.unpack('>I', file_bytes)[0]
  elif len(file_bytes) ==8:
    return struct.unpack('>Q', file_bytes)[0]

# get the top-level atom sizes
def get_atom_sizes(filename):
  byte_range = [0, 3]
  ftyp_size = get_integer(filename, byte_range)
  # error if ftyp_size not 24
  if ftyp_size != 24:
    raise ValueError('unexpected size of first atom')
  byte_range = [ftyp_size, ftyp_size + 3]
  mdat_size = get_integer(filename, byte_range)
  if mdat_size == 1:
    byte_range = [ftyp_size + 8, ftyp_size + 15]
    mdat_size = get_integer(filename, byte_range)
  byte_range = [ftyp_size + mdat_size, ftyp_size + mdat_size + 3]
  moov_size = get_integer(filename, byte_range)
  return ftyp_size, mdat_size, moov_size

# get the moov atom
# moov atom is returned as a string containing packed binary data
def get_moov_atom(filename):
  (ftyp_size, mdat_size, moov_size) = get_atom_sizes(filename)
  byte_range = [ftyp_size + mdat_size, ftyp_size + mdat_size + moov_size]
  #print("getting moov_atom") # print this for testing
  return get_bytes(filename, byte_range)

# get file creation timestamp (returns seconds from Unix epoch)
def get_timestamp(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  return struct.unpack('>I', moov_atom[20:24])[0]-2082844800 # adjust for difference between Unix and QuickTime epoch

# get frame count
def get_frame_count(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  stsz_pos = moov_atom.find(b'stsz') # searching for the ascii code is NOT IDEAL
  return struct.unpack('>I', moov_atom[stsz_pos+12:stsz_pos+16])[0]

# get frame sizes
def get_frame_sizes(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  frame_count = get_frame_count(filename, moov_atom)
  stsz_pos = moov_atom.find(b'stsz') # searching for the ascii code is NOT IDEAL
  frame_sizes = []
  for i in range(stsz_pos+16, stsz_pos+16+4*frame_count, 4):
    frame_sizes.append(struct.unpack('>I', moov_atom[i:i+4])[0])
  return frame_sizes

# get chunk count
def get_chunk_count(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  co64_pos = moov_atom.find(b'co64') # searching for the ascii code is NOT IDEAL
  return struct.unpack('>I', moov_atom[co64_pos+8:co64_pos+12])[0]

# get chunk offsets
def get_chunk_offsets(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  chunk_count = get_chunk_count(filename, moov_atom)
  co64_pos = moov_atom.find(b'co64') # searching for the ascii code is NOT IDEAL
  chunk_offsets = []
  for i in range(co64_pos+12, co64_pos+12+8*chunk_count, 8):
    chunk_offsets.append(struct.unpack('>Q', moov_atom[i:i+8])[0])
  return chunk_offsets

# get frame offsets
def get_frame_offsets(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  frame_sizes = get_frame_sizes(filename, moov_atom)
  chunk_offsets = get_chunk_offsets(filename, moov_atom)
  j = 0
  frame_offsets = []
  for chunk_pos in chunk_offsets:
    frame_offsets.append(chunk_pos)
    for i in range(0,5):
      try:
        frame_offsets.append(frame_offsets[-1] + frame_sizes[j])
        j = j+1
      except:
        break
    j = j+1
  return frame_offsets[0:len(frame_sizes)]

# build a single-frame avi file using frame_data
def get_avi_file(frame_data):
  avi_file = 'RIFF' + struct.pack('I', len(frame_data) + 5754) + 'AVI LIST' + \
    '\x38\x12\x00\x00\x68\x64\x72\x6c\x61\x76\x69\x68\x38\x00\x00\x00' + \
    '\x2b\x41\x00\x00\xc3\x3d\x09\x01\x00\x00\x00\x00\x10\x09\x00\x00' + \
    '\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x10\x00' + \
    '\x80\x07\x00\x00\x38\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
    '\x00\x00\x00\x00\x00\x00\x00\x00\x4c\x49\x53\x54\xe0\x10\x00\x00' + \
    '\x73\x74\x72\x6c\x73\x74\x72\x68\x38\x00\x00\x00\x76\x69\x64\x73' + \
    '\x61\x70\x63\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
    '\xe9\x03\x00\x00\x60\xea\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00' + \
    struct.pack('I', len(frame_data)) + '\xff\xff\xff\xff' + '\x00'*8  + \
    '\x80\x07\x38\x04\x73\x74\x72\x66\x28\x00\x00\x00\x28\x00\x00\x00' + \
    '\x80\x07\x00\x00\x38\x04\x00\x00\x01\x00\x18\x00\x61\x70\x63\x6e' + \
    '\x00\xec\x5e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
    '\x00\x00\x00\x00\x4a\x55\x4e\x4b\x18\x10\x00\x00\x04\x00\x00\x00' + \
    '\x00\x00\x00\x00\x30\x30\x64\x63\x00\x00\x00\x00\x00\x00\x00\x00' + \
    '\x00'*4096 + \
    '\x00\x00\x00\x00\x76\x70\x72\x70\x44\x00\x00\x00\x00\x00\x00\x00' + \
    '\x00\x00\x00\x00\x3c\x00\x00\x00\x80\x07\x00\x00\x38\x04\x00\x00' + \
    '\x09\x00\x10\x00\x80\x07\x00\x00\x38\x04\x00\x00\x01\x00\x00\x00' + \
    '\x38\x04\x00\x00\x80\x07\x00\x00\x38\x04\x00\x00\x80\x07\x00\x00' + \
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
    '\x4a\x55\x4e\x4b\x04\x01\x00\x00\x6f\x64\x6d\x6c\x64\x6d\x6c\x68' + \
    '\xf8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
    '\x00'*224 + \
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x4c\x49\x53\x54' + \
    '\x1a\x00\x00\x00\x49\x4e\x46\x4f\x49\x53\x46\x54\x0e\x00\x00\x00' + \
    '\x4c\x61\x76\x66\x35\x37\x2e\x35\x36\x2e\x31\x30\x30\x00\x4a\x55' + \
    '\x4e\x4b\xf8\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
    '\x00'*1006 + \
    'LIST' + struct.pack('I', len(frame_data) + 12) + 'movi' + \
    '\x30\x30\x64\x63' + struct.pack('I', len(frame_data)) + frame_data
  return avi_file

def _convert_to_array(frame):
  # define output datatype
  dt = np.uint8
  if frame.format.name in ('rgb48le', 'bgr48le', 'gray16le'):
    dt = np.dtype('uint16').newbyteorder('<')
  elif frame.format.name in ('rgb48be', 'bgr48be', 'gray16be'):
    dt = np.dtype('uint16').newbyteorder('>')

  # convert to numpy array
  if frame.format.name in ('rgb24', 'bgr24', 'rgb48le', 'rgb48be', 'bgr48le', 'bgr48be'):
    return np.frombuffer(frame.planes[0], dt).reshape(frame.height, frame.width, -1)
  elif frame.format.name in ('gray', 'gray16le', 'gray16be'):
    return np.frombuffer(frame.planes[0], dt).reshape(frame.height, frame.width)
  else:
    raise ValueError("%s format not supported. use one of: 'rgb24', 'bgr24', 'rgb48le', 'rgb48be', 'bgr48le', 'bgr48be', 'gray', 'gray16le', or 'gray16be'." % frame.format.name)

def decode_frame_data(frame_data, pix_fmt='rgb24'):
  packet = av.packet.Packet(frame_data)
  decoder = av.codec.CodecContext.create('prores', 'r')
  decoder.width = 1920
  decoder.height = 1080
  frame = decoder.decode(packet)[0].reformat(format=pix_fmt)
  return _convert_to_array(frame)

def get_frame(filename, frame_number, pix_fmt='rgb24', moov_atom=False):
  # get frame
  if "https://" in filename:
    frame_data = get_frame_data(filename, frame_number, moov_atom)
    return decode_frame_data(frame_data, pix_fmt)
  else:
    # need to test frame number here.
    # is this faster? maybe better to refactor so as to also use frame_data.
    container = av.open(filename)
    pts = int(frame_number*33366)
    container.seek(pts, whence='frame', backward=False)
    packet = next(container.demux())
    frame = packet.decode_one().reformat(format=pix_fmt)
    return _convert_to_array(frame)

# get frame data
def get_frame_data(filename, frame_number, moov_atom=False):
  if frame_number < 0:
    raise ValueError('frame_number must be a positive integer')
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  frame_sizes = get_frame_sizes(filename, moov_atom)
  if frame_number > len(frame_sizes) - 1:
    raise ValueError('frame_number exceeds number of frames in file')
  frame_offsets = get_frame_offsets(filename, moov_atom)
  byte_range = [frame_offsets[frame_number], frame_offsets[frame_number] +
    frame_sizes[frame_number] - 1]
  frame_data = get_bytes(filename, byte_range)
  return frame_data

# write frame to file
def write_frame(filename, frame_number, moov_atom=False, file_type='AVI'):
  if file_type=='AVI':
    if moov_atom:
      frame_data = get_frame_data(filename, frame_number, moov_atom)
    else:
      frame_data = get_frame_data(filename, frame_number)
    avi_file = get_avi_file(frame_data)
    outputfile = ('%s_%06.0f.avi' % (filename.split('/')[-1].split('.')[0], frame_number))
    f = open(outputfile, 'w')
    f.write(avi_file)
    f.close()

# get date range
def _get_date_range(start_date, end_date):
  for i in range(int ((end_date - start_date).days)):
    yield start_date + timedelta(i)

# get file list
def get_file_list():
  requests.packages.urllib3.disable_warnings()
  start_date = date(2015, 7, 9)
  end_date = date.today()
  file_list = []
  file_sizes = []
  for single_date in _get_date_range(start_date, end_date + timedelta(days=2)):
    indexfile = ("https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301" +
      single_date.strftime("/%Y/%m/%d/"))
    res = requests.get(indexfile, verify=False)
    for line in res.text.encode('utf-8').strip().splitlines():
      line = line.decode('utf-8')
      if 'mov' in line and 'md5' not in line:
        filename = (("https://rawdata.oceanobservatories.org/files/RS03ASHS/" +
        "PN03B/06-CAMHDA301" + single_date.strftime("/%Y/%m/%d/")) + line.split('\"')[5])
        file_list.append(filename)
        file_headers = requests.head(filename)
        try:
          file_sizes.append(int(file_headers.headers.get('Content-Length')))
        except:
          file_sizes.append(0)
  return file_list, file_sizes

# get raw data archive stats
def get_stats():
  requests.packages.urllib3.disable_warnings()
  start_date = date(2015, 7, 9)
  end_date = date.today()
  total_size = 0
  file_count = 0
  for single_date in _get_date_range(start_date, end_date + timedelta(days=2)):
    indexfile = ("https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301" +
      single_date.strftime("/%Y/%m/%d/"))
    res = requests.get(indexfile, verify=False)
    for line in res.text.encode('utf-8').strip().splitlines():
      if 'mov' in line and 'md5' not in line:
        filesize = line.strip().rsplit(' ', 1)[-1]
        if 'M' in filesize:
          mb = filesize.split('M')[0]
          total_size = total_size+float(mb)/1024/1024
          file_count = file_count + 1
        elif 'G' in filesize:
          gb = filesize.split('G')[0]
          total_size = total_size+float(gb)/1024
          file_count = file_count + 1
  return file_count, total_size

# get frame range from file (future function)

# main function to run when called directly, used mostly for testing
def main():
  pass

# main sentinel
if __name__ == "__main__":
  main()
