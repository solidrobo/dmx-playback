#!/usr/bin/env python3
import json
from datetime import datetime
from socket import socket, AF_INET, SOCK_DGRAM
from struct import unpack
from base64 import encodebytes

PORT = 6454
OUTPUT_NAME = 'recording'

soc=socket(AF_INET, SOCK_DGRAM)
soc.bind(('',PORT))
soc.settimeout(1)

messages = []
print ('started')
try:
  while True:
    try:
      message=soc.recvfrom(1024)
      packet = message[0]
      id, opcode, version = unpack('!8sHH', packet[:12])
      item = {'id': encodebytes(id).decode(), 'opcode' : opcode, 'version' : version}
      if opcode == 0x0050:
        id, opcode, version, seq, physical, universe, length =  unpack('!8sHHBBHH', message[0][:18])
        data = message[0][18:]
        extra = {
          'seq' : seq,
          'physical' : physical,
          'universe' : universe,
          'length' : length,
          'dmx' : encodebytes(data).decode()
        }
      elif opcode == 0x0052:
        aux, *rest = unpack('!H', packet[12:])
        extra = {
          'aux' : aux
        }
      else:
        pass
      messages.append(item | extra)

    except TimeoutError:
      continue

except KeyboardInterrupt:
  time = datetime.now().strftime("%Y%m%d%H%M%S")
  with open(f'{OUTPUT_NAME}-{time}.json','w') as f:
    json.dump(messages, f)
  print('done')