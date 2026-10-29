# Le do executavel Windows (UE 4.27) a assinatura registrada de UFUNCTIONs: parametros (nome, flags, offset) e tamanho.
# Varias classes podem ter funcao com o mesmo nome: lista todas as ocorrencias.
# Uso: ufunc_sig.py HumanitZ-Win64-Shipping.exe NomeDaFuncao...   (procura FClassFunctionLinkInfo {CreateFuncPtr, Nome})
# Flags: 0x80 Parm, 0x100 OutParm, 0x400 ReturnParm, 0x8000000 ReferenceParm, 0x2 ConstParm.
import struct, sys
d = open(sys.argv[1], 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]; nsec = struct.unpack_from('<H', d, pe + 6)[0]; opt = pe + 24
osz = struct.unpack_from('<H', d, pe + 20)[0]; base = struct.unpack_from('<Q', d, opt + 24)[0]; secs = []
for i in range(nsec):
    o = opt + osz + 40 * i; vs, va, rs, ra = struct.unpack_from('<IIII', d, o + 8); secs.append((va, vs, ra, rs))
def off(v):
    r = v - base
    for va, vs, ra, rs in secs:
        if va <= r < va + vs: return ra + r - va
def va_of(o):
    for va, vs, ra, rs in secs:
        if ra <= o < ra + rs: return base + va + o - ra
def cstr(v):
    o = off(v); return d[o:d.index(b'\0', o)].decode('latin1')
for name in sys.argv[2:]:
    s = d.find(name.encode() + b'\0'); found = False
    while s >= 0:
        pat = struct.pack('<Q', va_of(s)); i = d.find(pat)
        while i >= 0:
            zc = struct.unpack_from('<Q', d, i - 8)[0]; zo = off(zc) if 0x140000000 < zc < 0x150000000 else None
            if zo is not None:
                b = d[zo:zo + 0x40]; j = b.find(b'\x48\x8d\x15')
                if j >= 0:
                    fp = zc + j + 7 + struct.unpack_from('<i', b, j + 3)[0]; fo = off(fp)
                    if fo is not None:
                        q = struct.unpack_from('<9Q', d, fo)
                        try: nm = cstr(q[2])
                        except Exception: nm = None
                        if nm == name:
                            n = q[7] & 0xffffffff; ps = []
                            for p in struct.unpack_from('<%dQ' % n, d, off(q[6])) if n else []:
                                po = off(p); ps.append(f"{cstr(struct.unpack_from('<Q', d, po)[0])}(0x{struct.unpack_from('<Q', d, po + 16)[0] & 0xffffffff:x})")
                            print(f'{name}: tamanho 0x{q[5]:x}, {n} props: ' + ', '.join(ps)); found = True
            i = d.find(pat, i + 1)
        s = d.find(name.encode() + b'\0', s + 1)
    if not found: print(f'{name}: NAO ENCONTRADA (nao e UFUNCTION nesta build?)')
