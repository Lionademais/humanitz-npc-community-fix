# Lista as propriedades (FProperty) de nivel de classe de um export BPGC: nome, tipo, flags, struct
import sys, struct, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset import Asset
a = Asset(sys.argv[1]); d = a.d; exp = [e for e in a.exports if e['name'] == sys.argv[2]][0]
lo, hi = exp['off'], exp['off'] + exp['size']
q = lo
while q < hi - 40:
    try:
        t = a.fn(*struct.unpack_from('<ii', d, q)); n = a.fn(*struct.unpack_from('<ii', d, q + 8))
    except Exception: q += 1; continue
    if t.endswith('Property') and t[0].isupper() and n and struct.unpack_from('<i', d, q + 20)[0] in (1,):
        ad, es, pf = struct.unpack_from('<iiQ', d, q + 20)
        rep, = struct.unpack_from('<H', d, q + 36); rn = a.fn(*struct.unpack_from('<ii', d, q + 38))
        extra = ''
        if t in ('StructProperty', 'ObjectProperty', 'ClassProperty'):
            o, = struct.unpack_from('<i', d, q + 47); extra = a.obj(o) if o else ''
        print(f'@{q} {t:16s} {n:45s} sz={es:<5d} flags=0x{pf:x} net={bool(pf & 0x20)} repnotify={rn} {extra}')
        q += 47; continue
    q += 1
