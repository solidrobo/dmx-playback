#!/usr/bin/env python3
from json import load
from struct import pack
from base64 import b64decode
from time import sleep
from argparse import ArgumentParser
from glob import glob
import socket

IP = "2.255.255.255"
FRAME_RATE = 1/40

class ArtNet:
  VERSION = 14
  ID = 'Art-Net'
  PORT = 6454

  class Op:
    Dmx = 0x0050
    Sync= 0x0052

  def header(op_code):
    return pack('!8sHH', ArtNet.ID.encode(), op_code, ArtNet.VERSION)

  def syncPacket(aux=0):
    header = ArtNet.header(ArtNet.Op.Sync) 
    return pack('!12sH', header, aux)

  def dmxPacket(universe, data, sequence=0, physical=0):
    data_len = len(data)
    header = ArtNet.header(ArtNet.Op.Dmx)
    dmx = pack(f'!12sBBHH{data_len}s',
                header, sequence, physical, universe, data_len, data)
    return dmx

def parseRecording(path):
  # load json recording
  with open(path, 'r') as f:
    data = load(f)

  # parse json into raw bytes
  frames = []
  frame = None
  sequence_nr = 0
  for packet in data:
    opcode = packet['opcode']
    if opcode == ArtNet.Op.Sync:
      if frame:
        frames.append(frame)
      frame = []
      sequence_nr = sequence_nr % 255 + 1

    elif opcode == ArtNet.Op.Dmx:
      if frame is None:
        continue
      universe = packet['universe']
      data = b64decode(packet['dmx'])
      packet = ArtNet.dmxPacket(universe, data, sequence_nr)
      frame.append(packet)

    else:
      print(f'unknown opcode 0x{opcode:04X}')

  return frames

def playbackFrames(frames, framerate):
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      for frame in frames:
        for universe in frame:
          sock.sendto(universe, (IP, ArtNet.PORT))
        # send sync
        sync = ArtNet.syncPacket()
        sock.sendto(sync, (IP, ArtNet.PORT))
        # wait for next frame
        sleep(framerate)

if __name__ == '__main__':
  parser = ArgumentParser(description='Plays back .json format Art-Net DMX recordings')
  parser.add_argument("-d", help="directory to load recordings from",
                        dest="input_dir", default='./recordings')
  args = parser.parse_args()

  recordings = {}
  for file in glob(f'{args.input_dir}/**/*.json',recursive=True):
    print(f'loading {file}')
    frames = parseRecording(file)
    recordings[f'{file}'] = frames
  print('starting playback')
  try:
    while True:
      for recording in recordings.keys():
        print(f'playing {recording}')
        playbackFrames(recordings[recording], FRAME_RATE)
        print(f'done playing {recording}')
  except KeyboardInterrupt:
    pass

  print('done')

