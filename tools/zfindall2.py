# Varre o pak inteiro (blocos zlib) e extrai cada asset (uasset+uexp) que contem algum dos termos em qualquer bloco
import zlib, re, sys, os
p, outdir, terms = sys.argv[1], sys.argv[2], [t.encode() for t in sys.argv[3:]]
os.makedirs(outdir, exist_ok=True)
f = open(p, 'rb'); CH = 64 << 20; base = 0; hdr = re.compile(rb'\x78[\x01\x5e\x9c\xda]')
cur = None; buf = None; n = 0
def flush():
    global cur, buf, n
    if cur is not None and any(t in buf for t in terms):
        open(os.path.join(outdir, f'{cur}.bin'), 'wb').write(buf); n += 1
    cur = None; buf = None
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
        if data[:4] == b'\xc1\x83\x2a\x9e':
            flush(); cur = base + s; buf = bytearray()
        if cur is not None:
            buf += data
            if len(buf) > (64 << 20): cur = None; buf = None
    base += CH
flush(); print('extraidos', n)
