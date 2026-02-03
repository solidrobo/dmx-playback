from socket import socket, AF_INET, SOCK_DGRAM
from struct import unpack
import json
from base64 import encodebytes

soc=socket(AF_INET, SOCK_DGRAM)
soc.bind(('',6454))
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
        id, opcode, version, seq, physical, sub_uni, net, length =  unpack('!8sHHBBBBH', message[0][:18])
        data = message[0][18:]
        extra = {
          'seq' : seq,
          'physical' : physical,
          'sub' : sub_uni,
          'net' : net,
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
  with open('dump1.json','w') as f:
    json.dump(messages, f)
  print('done')