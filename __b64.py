#!python3
import base64
import sys

if len(sys.argv) < 3:
  print("Use b64 infile outfile")
  exit()

with open(sys.argv[1]) as b64file:
    b64data = b64file.read()

with open(sys.argv[2], 'wb') as file:
    file.write(base64.b64decode(b64data))
 