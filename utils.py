import sys, struct

def raw_packet_to_str(pkt):
  """
  Returns the string representation of a raw HCI packet.
  """
  if sys.version_info > (3, 0):
    return ''.join('%02x' % struct.unpack("B", bytes([x]))[0] for x in pkt)
  else:
    return ''.join('%02x' % struct.unpack("B", x)[0] for x in pkt)

def parse_struct(data, struct):
  result = {}
  i = 0
  for key in struct:
    if key == 999:
      result[key] = data[i:]
    else:
      result[key] = data[i:i + struct[key] * 2]
    i = i + struct[key] * 2
  return result

