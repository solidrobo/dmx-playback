from json import load
from struct import pack
from base64 import b64decode
from time import sleep
import socket

FILENAME = 'recording-20260203130920.json'
IP = "2.255.255.255"
PORT = 6454
FRAME_RATE = 1/40

with open(FILENAME, 'r') as f:
  data = load(f)

frames = []
frame = None
counter = 0
for packet in data:
  if packet['opcode'] == 82:
    if frame and len(frame):
      frames.append(frame)
    frame = []
  else:
    if frame is None:
      continue

    id = b64decode(packet['id'])
    opcode = packet['opcode']
    version = packet['version']
    #counter = counter % 255 + 1
    counter = 0
    physical = packet['physical']
    sub = packet['sub']
    net = packet['net']
    length = packet['length']
    dmx = b64decode(packet['dmx'])
    msg = pack(f'!8sHHBBBBH{length}s',
              id, opcode, version, counter, physical, sub, net, length, dmx)
    frame.append(msg)

try:
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      
      while True:
        for frame in frames:
          for universe in frame:
            sock.sendto(universe, (IP, PORT))
          sync = pack('!8sHHH', 'Art-Net'.encode(), 0x0052, 14, 0)
          sock.sendto(sync, (IP, PORT))
          sleep(FRAME_RATE)

except KeyboardInterrupt:
  pass

print('done')