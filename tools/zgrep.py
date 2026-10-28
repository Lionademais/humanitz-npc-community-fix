# Varre o pak e, para cada bloco que contem o termo, informa o asset (inicio) e o nome principal
import zlib, re, sys
p, terms = sys.argv[1], [t.encode() for t in sys.argv[2:]]
f = open(p, 'rb'); CH = 64 << 20; base = 0; hdr = re.compile(rb'\x78[\x01\x5e\x9c\xda]'); cur = None; curname = '?'
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
            cur = base + s; ns = re.findall(rb'(?:W|WBP|UI|BP|WB)_[A-Za-z0-9_]+_C\x00', data[:65536]); curname = ns[0][:-1].decode() if ns else '?'
        for t in terms:
            i = data.find(t)
            if i >= 0:
                ctx = re.sub(rb'[^\x20-\x7e]', b'.', data[max(0, i-60):i+100]).decode()
                print(f'{t.decode()!r} asset@{cur} {curname} :: {ctx}', flush=True)
    base += CH
