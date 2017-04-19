#!/usr/bin/env python
# This is a Python module for interacting with data from the OOI CamHD
# seafloor camera system stored in the raw data archive. It can be used to
# obtain information about these files or obtain individual frames without
# downloading entire video files. The module can also work with video files
# stored on the local filesystem.
#
# Timothy Crone (tjcrone@gmail.com)

# imports
import subprocess, struct, sys, requests
from datetime import date, timedelta

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

# get frame count
def get_frame_count(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  stsz_pos = moov_atom.find('stsz') # searching for the ascii code is NOT IDEAL
  return struct.unpack('>I', moov_atom[stsz_pos+12:stsz_pos+16])[0]

# get frame sizes
def get_frame_sizes(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  frame_count = get_frame_count(filename, moov_atom)
  stsz_pos = moov_atom.find('stsz') # searching for the ascii code is NOT IDEAL
  frame_sizes = []
  for i in range(stsz_pos+16, stsz_pos+16+4*frame_count, 4):
    frame_sizes.append(struct.unpack('>I', moov_atom[i:i+4])[0])
  return frame_sizes

# get chunk count
def get_chunk_count(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  co64_pos = moov_atom.find('co64') # searching for the ascii code is NOT IDEAL
  return struct.unpack('>I', moov_atom[co64_pos+8:co64_pos+12])[0]

# get chunk offsets
def get_chunk_offsets(filename, moov_atom=False):
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  chunk_count = get_chunk_count(filename, moov_atom)
  co64_pos = moov_atom.find('co64') # searching for the ascii code is NOT IDEAL
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

# get frame data
def get_frame_data(filename, frame_number, moov_atom=False):
  if frame_number < 0:
    raise ValueError('frame_number must be a positive integer')
  if not moov_atom:
    moov_atom = get_moov_atom(filename)
  frame_sizes = get_frame_sizes(filename, moov_atom)
  if frame_number > len(frame_sizes):
    raise ValueError('frame_number exceeds number of frames in file')
  frame_offsets = get_frame_offsets(filename, moov_atom)
  byte_range = [frame_offsets[frame_number - 1], frame_offsets[frame_number - 1] +
    frame_sizes[frame_number - 1] - 1]
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
  for single_date in _get_date_range(start_date, end_date + timedelta(days=2)):
    indexfile = ("https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301" +
      single_date.strftime("/%Y/%m/%d/"))
    res = requests.get(indexfile, verify=False)
    for line in res.text.encode('utf-8').strip().splitlines():
      if 'mov' in line:
        file_list.append(("https://rawdata.oceanobservatories.org/files/RS03ASHS/" +
        "PN03B/06-CAMHDA301" + single_date.strftime("/%Y/%m/%d/")) + line.split('\"')[5])
  return file_list

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
      if 'mov' in line:
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
  # file to test
  #filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/13/CAMHDA301-20161113T000000Z.mov'
  #filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2015/07/09/CAMHDA301-20150709T121400Z.mov'
  #filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2015/11/25/CAMHDA301-20151125T150000Z.mov'
  #filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/11/20/CAMHDA301-20161120T180000Z.camhd_prores_001744.mov' # new file
  #filename = 'https://rawdata.oceanobservatories.org/files/RS03ASHS/PN03B/06-CAMHDA301/2016/01/27/CAMHDA301-20160127T180000Z.mov'
  #filename = '/Users/tjc/research/ooi/misc/CAMHDA301-20161113T000000Z.mov'

  # test avi writer
  #frame_number = int(sys.argv[1])
  #moov_atom = get_moov_atom(filename)
  #frame_count = get_frame_count(filename, moov_atom)
  #print(frame_count)
  #frame_number = 4976
  #write_frame(filename, frame_number, moov_atom)

  #write_frame(filename, frame_number)

  #(total_size, file_count) = get_stats()

  #print total_size
  #print file_count

  # get atom positions
  #(ftyp_size, mdat_size, moov_size) = get_atom_sizes(filename)
  #print ftyp_size
  #print mdat_size
  #print moov_size
  
  # get moov atom
  #moov_atom = get_moov_atom(filename)
  #print len(moov_atom)
  #sys.stdout.write(moov_atom)

  #frame_count = get_frame_count(filename, moov_atom)
  #print frame_count

  # get frame sizes
  #frame_sizes = get_frame_offsets(filename, moov_atom)
  #for i in frame_sizes:
  #  sys.stdout.write('%i\n' % i)

  # test byte range
  #byte_range = [3901, 3916]
  #file_bytes = get_bytes(filename, byte_range)
  #sys.stdout.write(file_bytes)

  # get_file_list test
  #file_list = get_file_list()
  #print len(file_list)

  #for filename in file_list:
  #  print filename
  #  try:
  #    (ftyp_size, mdat_size, moov_size) = get_atom_sizes(filename)
  #    print ftyp_size
  #    print mdat_size
  #    print moov_size
  #  except:
  #    print "no good"
  #    return

  # test avi writer
  #frame_number = int(sys.argv[1])
  #write_frame(filename, frame_number)

  # get moov atom
  #moov_atom = get_moov_atom(filename)
  #print type(moov_atom)

  # get frame sizes
  #frame_sizes = get_frame_sizes(filename, moov_atom)
  #for i in frame_sizes:
  #  sys.stdout.write('%i\n' % i)

  # get frame offsets
  #frame_offsets = get_frame_offsets(filename, moov_atom)
  #for i in frame_offsets:
  #  sys.stdout.write('%i\n' % i)

  #sys.stdout.write(frame_data)

  #print len(frame_data)

  #avi_file = get_avi_header() + frame_data

  #frame_number = 600
  #frame_number = int(sys.argv[1])
  #frame_data = get_frame_data(filename, frame_number, moov_atom)
  #avi_file = get_avi_file(frame_data)
  #sys.stdout.write(avi_file)

  # write this avi to a temporary file
  #outputfile = ('test_frame_%i_camhd.avi' % frame_number)
  #f = open(outputfile, 'w')
  #f.write(avi_file)
  #f.close()
  #quit()

  #for frame_number in range(487,498):
  #for frame_number in range(1,len(frame_sizes)+1):
  #  print frame_number
  #  frame_data = get_frame_data(filename, frame_number, moov_atom)
    #print frame_sizes[frame_number-1]
    #print len(frame_data)
  #  avi_file = get_avi_file(frame_data)
  #  outputfile = ('test_frame_%05.0f_camhd.avi' % frame_number)
  #  f = open(outputfile, 'w')
  #  f.write(avi_file)
  #  f.close

  #for frame_number in range(487,498):
  #  print frame_number
  #  frame_data = get_frame_data(filename, frame_number, moov_atom)
  #  f = open('tmp.avi', 'w')
  #  avi_file = get_avi_file(frame_data)
  #  f.write(avi_file)
  #  f.close

  #  outputfile = ('tmp_%i.png' % frame_number)
  #  ff = FFmpeg(inputs = {'tmp.avi': None}, outputs = {outputfile: None})
  #  ff.run()

    #cmd = ('ffmpeg -y -v error -i tmp.avi -f framemd5 tmp.md5')
    #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    #cmd = ('tail -n 1 tmp.md5 >> allmd5')
    #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    #framemd5 = p.communicate()[0]
    #print framemd5
  #return file_bytes

  # convert to yuv rawvideo 
  #  cmd = ('curl --header "Range: bytes=%i-%i" -k -s ' % 
  #    (byte_range[0], byte_range[1])) + filename
  #  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

# main sentinel
if __name__ == "__main__":
  main()
