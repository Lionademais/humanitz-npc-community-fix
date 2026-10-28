# Leitor minimo de uasset UE4.27 cozinhado (uasset+uexp concatenados): nomes, imports, exports
import struct
class Asset:
    def __init__(s, path):
        d = s.d = open(path, 'rb').read()
        o = 8; o += 4; o += 8
        ncv = struct.unpack_from('<i', d, o)[0]; o += 4 + ncv * 20
        s.header_size = struct.unpack_from('<i', d, o)[0]; o += 4
        sl = struct.unpack_from('<i', d, o)[0]; o += 4 + sl
        s.pkg_flags, nc, no, gc, go, ec, eo, ic, io = struct.unpack_from('<Iiiiiiiii', d, o)
        s.names = []; p = no
        for _ in range(nc):
            l = struct.unpack_from('<i', d, p)[0]; p += 4
            if l < 0: n = d[p:p + (-l) * 2].decode('utf-16-le')[:-1]; p += (-l) * 2
            else: n = d[p:p + l - 1].decode('latin1'); p += l
            p += 4; s.names.append(n)
        s.imports = []
        for i in range(ic):
            cp, cpn, cn, cnn, outer, on, onn = struct.unpack_from('<iiiiiii', d, io + 28 * i)
            s.imports.append((s.fn(cn, cnn), outer, s.fn(on, onn)))
        s.exports = []
        for i in range(ec):
            b = eo + 104 * i
            ci, si, ti, oi, on, onn, fl = struct.unpack_from('<iiiiiiI', d, b)
            ss, so = struct.unpack_from('<qq', d, b + 28)
            s.exports.append(dict(cls=ci, sup=si, outer=oi, name=s.fn(on, onn), size=ss, off=so))
    def fn(s, i, n=0):
        if not (0 <= i < len(s.names)): return f'<name {i}>'
        return s.names[i] + (f'_{n-1}' if n else '')
    def obj(s, idx):
        if idx == 0: return 'null'
        if idx < 0:
            c, outer, n = s.imports[-idx - 1]
            return (s.obj(outer) + '.' if outer else '') + n
        e = s.exports[idx - 1]
        return e['name']
