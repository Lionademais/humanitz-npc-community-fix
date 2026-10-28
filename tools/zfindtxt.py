# Varre o pak e, para cada termo (ASCII ou UTF-16), mostra o asset (nomes BP_/DT_ do cabecalho) e o contexto
import zlib, re, sys
p, terms = sys.argv[1], sys.argv[2:]
pats = [(t, re.compile(re.escape(t.encode()) + b'|' + re.escape(t.encode('utf-16-le')), re.I)) for t in terms]
f = open(p, 'rb'); CH = 64 << 20; base = 0; hdr = re.compile(rb'\x78[\x01\x5e\x9c\xda]'); cur = '?'
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
            ns = re.findall(rb'(?:BP|DT|ST|S|E)_[A-Za-z0-9_]+\x00', data[:65536]); cur = ns[0][:-1].decode() if ns else '?'
        for t, rx in pats:
            for mm in rx.finditer(data):
                ctx = re.sub(rb'[^\x20-\x7e]+', b'.', data[max(0, mm.start()-200):mm.end()+120].replace(b'\x00', b'')).decode()
                print(f'[{t}] asset~{cur} @{base+s}: {ctx}', flush=True)
    base += CH
