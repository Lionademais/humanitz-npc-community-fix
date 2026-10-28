# Reconstrutor minimo de pacote UE4.27 cozinhado (uasset+uexp concatenados, unversioned).
# Permite acrescentar nomes/imports/exports, trocar blobs de exports e reescrever dependencias de preload.
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset import Asset

class Pkg:
    def __init__(s, path):
        s.a = Asset(path); d = s.d = bytearray(s.a.d)
        o = 20; n = struct.unpack_from('<i', d, o)[0]; o += 4 + 20 * n
        s.o_total = o; o += 4
        l = struct.unpack_from('<i', d, o)[0]; o += 4 + l
        o += 4  # pkg flags
        s.o_names = o; o += 8
        s.o_gather = o; o += 8
        s.o_exports = o; o += 8
        s.o_imports = o; o += 8
        s.o_depends = o; o += 4
        s.o_softpkg = o; o += 8
        s.o_searchable = o; o += 4
        s.o_thumb = o; o += 4
        o += 16; g = struct.unpack_from('<i', d, o)[0]; o += 4; s.o_gens = [o + 8 * i for i in range(g)]; o += 8 * g
        for _ in range(2):
            o += 10; l = struct.unpack_from('<i', d, o)[0]; o += 4 + l
        o += 4; assert struct.unpack_from('<i', d, o)[0] == 0; o += 4; o += 4
        n = struct.unpack_from('<i', d, o)[0]; assert n == 0; o += 4
        s.o_assetreg = o; o += 4
        s.o_bulk = o; o += 8
        s.o_worldtile = o; o += 4
        n = struct.unpack_from('<i', d, o)[0]; o += 4 + 4 * n
        s.o_preload = o; o += 8
        s.summary_end = o
        s.names = list(s.a.names)
        s.new_names = []; s.new_imports = []
        s.header_size = struct.unpack_from('<i', d, s.o_total)[0]
        nc, no = struct.unpack_from('<ii', d, s.o_names); ec, eo = struct.unpack_from('<ii', d, s.o_exports)
        ic, io = struct.unpack_from('<ii', d, s.o_imports)
        s.ec = ec
        s.exp_entries = [bytearray(d[eo + 104 * i:eo + 104 * (i + 1)]) for i in range(ec)]
        s.blobs = {i: bytes(d[e['off']:e['off'] + e['size']]) for i, e in enumerate(s.a.exports)}
        s.tail = bytes(d[max(e['off'] + e['size'] for e in s.a.exports):])
        pc, po = struct.unpack_from('<ii', d, s.o_preload)
        pre = [struct.unpack_from('<i', d, po + 4 * k)[0] for k in range(pc)]
        s.deps = []
        for i in range(ec):
            f, c1, c2, c3, c4 = struct.unpack_from('<iiiii', s.exp_entries[i], 84)
            if f < 0: s.deps.append(([], [], [], []))
            else:
                b = pre[f:f + c1 + c2 + c3 + c4]
                s.deps.append((b[:c1], b[c1:c1 + c2], b[c1 + c2:c1 + c2 + c3], b[c1 + c2 + c3:]))
        s.orig_pre = pre; s.deps_changed = set()
        # secoes do cabecalho, para o layout de saida
        s.sec_names = bytes(d[no:io]); s.sec_imports = bytes(d[io:io + 28 * ic])
        dep_o = struct.unpack_from('<i', d, s.o_depends)[0]; ar_o = struct.unpack_from('<i', d, s.o_assetreg)[0]
        assert eo + 104 * ec == dep_o and io + 28 * ic == eo and dep_o < ar_o < po
        assert struct.unpack_from('<i', d, s.o_softpkg)[0] == 0 and struct.unpack_from('<i', d, s.o_searchable)[0] == 0
        assert struct.unpack_from('<i', d, s.o_thumb)[0] == 0 and struct.unpack_from('<i', d, s.o_worldtile)[0] == 0
        assert struct.unpack_from('<ii', d, s.o_gather) == (0, 0)
        s.sec_depends = [bytes(d[dep_o + 4 * i:dep_o + 4 * i + 4]) for i in range(ec)]
        assert all(x == b'\0\0\0\0' for x in s.sec_depends), 'DependsMap nao vazio nao suportado'
        s.sec_assetreg = bytes(d[ar_o:po]); assert po + 4 * pc == s.header_size
        s.summary = bytes(d[:no])
    def i32(s, off): return struct.unpack_from('<i', s.d, off)[0]
    def name(s, n):
        """indice do FName (acrescenta se nao existir)"""
        if n in s.names: return s.names.index(n)
        s.names.append(n); s.new_names.append(n); return len(s.names) - 1
    def all_imports(s):
        return s.a.imports + [(x[1], x[2], x[3]) for x in s.new_imports]
    def find_import(s, cls, name, outer=None):
        for i, (c, o, nm) in enumerate(s.all_imports()):
            if c == cls and nm == name and (outer is None or o == outer): return -(i + 1)
        return None
    def add_import(s, cpkg, cls, outer, name):
        f = s.find_import(cls, name, outer)
        if f: return f
        s.new_imports.append((cpkg, cls, outer, name))
        return -(len(s.a.imports) + len(s.new_imports))
    def export_index(s, name):
        """indice (1-based) de um export pelo nome"""
        for i in range(s.ec):
            if s.export_name(i) == name: return i + 1
    def export_name(s, i):
        n, num = struct.unpack_from('<ii', s.exp_entries[i], 16)
        return s.names[n] + (f'_{num - 1}' if num else '')
    def add_export(s, template_idx, name, outer, blob, deps):
        """acrescenta um export copiando os campos de classe/template de outro export (indice 0-based)"""
        e = bytearray(s.exp_entries[template_idx])
        base, num = name, 0
        struct.pack_into('<iii', e, 12, outer, s.name(base), num)
        s.exp_entries.append(e); s.blobs[s.ec] = bytes(blob); s.deps.append(deps); s.deps_changed.add(s.ec)
        s.sec_depends.append(b'\0\0\0\0'); s.ec += 1
        return s.ec
    def set_deps(s, i, deps):
        s.deps[i] = deps; s.deps_changed.add(i)
    def save(s, path_uasset, path_uexp):
        nb = bytearray()
        for cpkg, cls, outer, name in s.new_imports:
            s.name(cpkg); s.name(cls); s.name(name)
        for n in s.new_names:
            b = n.encode('latin1') + b'\0'; nb += struct.pack('<i', len(b)) + b + b'\0\0\0\0'
        ib = bytearray()
        for cpkg, cls, outer, name in s.new_imports:
            ib += struct.pack('<iiiiiii', s.name(cpkg), 0, s.name(cls), 0, outer, s.name(name), 0)
        # dependencias de preload: mantem as originais; as alteradas/novas vao para o fim do array
        pre = list(s.orig_pre)
        for i in range(s.ec):
            if i in s.deps_changed:
                a, b, c, dd = s.deps[i]
                first = len(pre) if (a or b or c or dd) else -1
                pre += a + b + c + dd
                struct.pack_into('<iiiii', s.exp_entries[i], 84, first, len(a), len(b), len(c), len(dd))
        names = s.sec_names + nb; imports = s.sec_imports + ib
        no = len(s.summary); io = no + len(names); eo = io + len(imports)
        dep_o = eo + 104 * s.ec; ar_o = dep_o + 4 * s.ec; po = ar_o + len(s.sec_assetreg)
        hs = po + 4 * len(pre)
        # exports: blobs na ordem original de offset; novos no fim
        order = sorted(range(len(s.a.exports)), key=lambda i: s.a.exports[i]['off']) + list(range(len(s.a.exports), s.ec))
        body = bytearray(); pos = hs
        for i in order:
            b = s.blobs[i]; struct.pack_into('<qq', s.exp_entries[i], 28, len(b), pos); body += b; pos += len(b)
        body += s.tail
        summ = bytearray(s.summary)
        struct.pack_into('<i', summ, s.o_total, hs)
        struct.pack_into('<ii', summ, s.o_names, len(s.names), no)
        struct.pack_into('<ii', summ, s.o_exports, s.ec, eo)
        struct.pack_into('<ii', summ, s.o_imports, len(s.a.imports) + len(s.new_imports), io)
        struct.pack_into('<i', summ, s.o_depends, dep_o)
        struct.pack_into('<i', summ, s.o_assetreg, ar_o)
        struct.pack_into('<ii', summ, s.o_preload, len(pre), po)
        for g in s.o_gens: struct.pack_into('<ii', summ, g, s.ec, len(s.names))
        struct.pack_into('<q', summ, s.o_bulk, hs + len(body) - 4)
        hdr = summ + names + imports + b''.join(s.exp_entries) + b''.join(s.sec_depends) + s.sec_assetreg + b''.join(struct.pack('<i', x) for x in pre)
        assert len(hdr) == hs
        open(path_uasset, 'wb').write(hdr); open(path_uexp, 'wb').write(body)
        return bytes(hdr + body)
