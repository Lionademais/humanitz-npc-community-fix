# Lista os parametros/locais (ChildProperties) de exports de funcao
import sys, struct, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset import Asset
EXTRA = {'StructProperty': 4, 'ObjectProperty': 4, 'ClassProperty': 8, 'ByteProperty': 4, 'BoolProperty': 6, 'EnumProperty': 4, 'SoftObjectProperty': 4,
         'InterfaceProperty': 4, 'WeakObjectProperty': 4, 'SoftClassProperty': 8, 'DelegateProperty': 4, 'MulticastInlineDelegateProperty': 4}
def field(a, b, p):
    t = a.fn(*struct.unpack_from('<ii', b, p)); n = a.fn(*struct.unpack_from('<ii', b, p + 8))
    of, ad, es, pf = struct.unpack_from('<IiiQ', b, p + 16); q = p + 47; ex = ''
    if t in ('ArrayProperty', 'SetProperty'):
        r, q = field(a, b, q); ex = f'<{r}>'
    elif t == 'MapProperty':
        k, q = field(a, b, q); v, q = field(a, b, q); ex = f'<{k},{v}>'
    elif t == 'EnumProperty':
        u, q = field(a, b, q + 0); ex = f'enum'  # underlying + enum
        ex += ' ' + a.obj(struct.unpack_from('<i', b, q)[0]); q += 4
    else:
        k = EXTRA.get(t, 0)
        if k >= 4: ex = a.obj(struct.unpack_from('<i', b, q)[0])
        q += k
    return f'{n}:{t}{ex} flags=0x{pf:x}', q
def params(a, e):
    b = a.d[e['off']:e['off'] + e['size']]; p = 8 + 4 + 4
    n = struct.unpack_from('<i', b, p)[0]; p += 4 + 4 * n
    n = struct.unpack_from('<i', b, p)[0]; p += 4; out = []
    for _ in range(n):
        s, p = field(a, b, p); out.append(s)
    return out, p
if __name__ == '__main__':
    a = Asset(sys.argv[1])
    for e in a.exports:
        if e['name'] in sys.argv[2:]:
            ps, end = params(a, e); print(e['name'], ps)
