# Varre os blocos zlib do pak e lista caminhos /Game/... que terminam nos nomes pedidos
import zlib, re, sys
p, names = sys.argv[1], sys.argv[2:]
rx = re.compile(rb'/Game/[A-Za-z0-9_/\-]*/(?:' + b'|'.join(re.escape(n.encode()) for n in names) + rb')\x00')
f = open(p, 'rb'); CH = 64 << 20; base = 0; hdr = re.compile(rb'\x78[\x01\x5e\x9c\xda]'); found = set()
while True:
    f.seek(base); m = f.read(CH + 262144)
    if len(m) < 16: break
    pos = 0
    for h in hdr.finditer(m, 0, min(CH, len(m))):
        s = h.start()
        if s < pos: continue
        d = zlib.decompressobj()
        try: data = d.decompress(m[s:s+262144], 1 << 20)
        except zlib.error: continue
        if not d.eof or len(data) < 16: continue
        pos = s + (min(262144, len(m)-s) - len(d.unused_data))
        for x in rx.findall(data):
            if x not in found: found.add(x); print(x[:-1].decode(), flush=True)
    base += CH
