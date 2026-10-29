# Extrai todos os arquivos .locres de um pak (procura o magic do locres nos blocos zlib e nos dados sem compressao).
# Uso: zlocres.py pak saida_dir   -> saida_dir/<offset>.locres (concatena blocos seguintes do mesmo arquivo)
import zlib, re, sys, os
p, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
MAGIC = bytes.fromhex('0e1474754a03fc4a15909dc3377f1b')[:16] if False else bytes.fromhex('0E147475674A03FC4A15909DC3377F1B')
f = open(p, 'rb'); CH = 64 << 20; base = 0; hdr = re.compile(rb'\x78[\x01\x5e\x9c\xda]'); cur = None; buf = None; n = 0
def flush():
    global cur, buf, n
    if cur is not None: open(os.path.join(out, f'{cur}.locres'), 'wb').write(buf); n += 1
    cur = None; buf = None
while True:
    f.seek(base); m = f.read(CH + 262144)
    if len(m) < 16: break
    for k in re.finditer(re.escape(MAGIC), m[:CH]):  # sem compressao
        s = k.start(); open(os.path.join(out, f'raw{base+s}.locres'), 'wb').write(m[s:s+8 << 20])
    pos = 0
    for h in hdr.finditer(m, 0, min(CH, len(m))):
        s = h.start()
        if s < pos: continue
        d = zlib.decompressobj()
        try: data = d.decompress(m[s:s+262144], 1 << 20)
        except zlib.error: continue
        if not d.eof or len(data) < 16: continue
        pos = s + (min(262144, len(m) - s) - len(d.unused_data))
        if data[:16] == MAGIC: flush(); cur = base + s; buf = bytearray(data); continue
        if cur is not None:
            if data[:4] == b'\xc1\x83\x2a\x9e' or len(buf) > (32 << 20): flush()
            else: buf += data
    base += CH
flush(); print('locres', n)
