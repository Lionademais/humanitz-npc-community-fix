# Le um .locres (UE4, versoes 0-3) -> dict {(namespace, key): texto}. Uso: locres.py arquivo [chave...]
import struct, sys
def fstr(d, p):
    n = struct.unpack_from('<i', d, p)[0]; p += 4
    if n < 0: n = -n; s = d[p:p + 2 * n].decode('utf-16-le', 'replace').rstrip('\0'); return s, p + 2 * n
    return d[p:p + n].decode('latin1').rstrip('\0'), p + n
def read(path):
    d = open(path, 'rb').read(); ver = d[16]; p = 17
    off = struct.unpack_from('<q', d, p)[0]; p += 8
    if ver >= 2: p += 4
    q = off; cnt = struct.unpack_from('<i', d, q)[0]; q += 4; strs = []
    for _ in range(cnt):
        s, q = fstr(d, q); strs.append(s)
        if ver >= 3: q += 4
    out = {}; nns = struct.unpack_from('<I', d, p)[0]; p += 4
    for _ in range(nns):
        if ver >= 2: p += 4
        ns, p = fstr(d, p); nk = struct.unpack_from('<I', d, p)[0]; p += 4
        for _ in range(nk):
            if ver >= 2: p += 4
            k, p = fstr(d, p); p += 4; i = struct.unpack_from('<i', d, p)[0]; p += 4
            out[(ns, k)] = strs[i] if 0 <= i < len(strs) else None
    return out
if __name__ == '__main__':
    t = read(sys.argv[1]); print(len(t), 'entradas')
    for k in sys.argv[2:]: print(k, [v for (n, kk), v in t.items() if kk == k])
