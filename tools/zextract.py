# Descomprime e concatena os blocos zlib entre start e end (um asset .uasset+.uexp) num arquivo
import zlib, re, sys
p, start, end, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
f = open(p, 'rb'); f.seek(start); m = f.read(end - start)
pos = 0; buf = bytearray(); marks = []
for h in re.compile(rb'\x78[\x01\x5e\x9c\xda]').finditer(m):
    s = h.start()
    if s < pos: continue
    d = zlib.decompressobj()
    try: data = d.decompress(m[s:s+262144], 1 << 20)
    except zlib.error: continue
    if not d.eof or len(data) < 16: continue
    pos = s + (min(262144, len(m) - s) - len(d.unused_data))
    marks.append((start + s, len(buf), len(data))); buf += data
open(out, 'wb').write(buf)
for a in marks: print(a)
