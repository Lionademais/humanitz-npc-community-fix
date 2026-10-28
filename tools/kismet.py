# Desmontador simples de bytecode Kismet (UE4.27, serializado). Mostra offsets em disco e em memoria.
import struct
class Dis:
    def __init__(s, asset, start, end):
        s.a, s.d, s.p, s.end = asset, asset.d, start, end
        s.mem = 0  # offset em memoria (ponteiros = 8 bytes, FName = 12)
        s.out = []
    def u8(s): v = s.d[s.p]; s.p += 1; s.mem += 1; return v
    def u16(s): v = struct.unpack_from('<H', s.d, s.p)[0]; s.p += 2; s.mem += 2; return v
    def i32(s): v = struct.unpack_from('<i', s.d, s.p)[0]; s.p += 4; s.mem += 4; return v
    def u32(s): v = struct.unpack_from('<I', s.d, s.p)[0]; s.p += 4; s.mem += 4; return v
    def f32(s): v = struct.unpack_from('<f', s.d, s.p)[0]; s.p += 4; s.mem += 4; return v
    def name(s):
        i, n = struct.unpack_from('<ii', s.d, s.p); s.p += 8; s.mem += 12; return s.a.fn(i, n)
    def obj(s):
        i = struct.unpack_from('<i', s.d, s.p)[0]; s.p += 4; s.mem += 8; return s.a.obj(i)
    def prop(s):
        n = struct.unpack_from('<i', s.d, s.p)[0]; s.p += 4
        path = []
        for _ in range(n):
            i, nn = struct.unpack_from('<ii', s.d, s.p); s.p += 8; path.append(s.a.fn(i, nn))
        owner = struct.unpack_from('<i', s.d, s.p)[0]; s.p += 4
        s.mem += 8
        return '.'.join(path) or 'null'
    def astr(s):
        e = s.d.index(b'\0', s.p); v = s.d[s.p:e].decode('latin1'); s.mem += e - s.p + 1; s.p = e + 1; return v
    def wstr(s):
        q = s.p
        while s.d[q:q+2] != b'\0\0': q += 2
        v = s.d[s.p:q].decode('utf-16-le'); s.mem += q - s.p + 2; s.p = q + 2; return v
    def params(s):
        a = []
        while s.d[s.p] != 0x16: a.append(s.expr())
        s.u8(); return a
    def until(s, t):
        a = []
        while s.d[s.p] != t: a.append(s.expr())
        s.u8(); return a
    def expr(s):
        t = s.u8()
        if t in (0x00, 0x01, 0x02, 0x48, 0x6C): return f'{ {0:"L",1:"I",2:"D",0x48:"OUT",0x6C:"SP"}[t] }:{s.prop()}'
        if t == 0x04: return f'return {s.expr()}'
        if t == 0x06: return f'jump @{s.u32()}'
        if t == 0x07: o = s.u32(); return f'if not ({s.expr()}) jump @{o}'
        if t == 0x09: s.u16(); s.u8(); return f'assert {s.expr()}'
        if t == 0x0B: return 'nothing'
        if t == 0x0F: p = s.prop(); return f'let {s.expr()} = {s.expr()}'
        if t in (0x12, 0x19, 0x1A):
            ctx = s.expr(); s.u32(); s.prop(); return f'{ctx}->{s.expr()}'
        if t in (0x13, 0x2E, 0x52, 0x54, 0x55): o = s.obj(); return f'cast<{o}>({s.expr()})'
        if t in (0x14, 0x5F, 0x60, 0x43, 0x44): a = s.expr(); return f'let {a} = {s.expr()}'
        if t == 0x15: return 'endparm'
        if t == 0x17: return 'self'
        if t == 0x18: s.u32(); return f'skip {s.expr()}'
        if t in (0x1B, 0x45): n = s.name(); return f'{n}({", ".join(s.params())})'
        if t in (0x1C, 0x46, 0x68, 0x63): o = s.obj(); return f'{o}({", ".join(s.params())})'
        if t == 0x1D: return str(s.i32())
        if t == 0x1E: return f'{s.f32():g}'
        if t == 0x1F: return repr(s.astr())
        if t == 0x20: return f'obj({s.obj()})'
        if t == 0x21: return f'name({s.name()})'
        if t in (0x22, 0x23): return f'vec({s.f32():g},{s.f32():g},{s.f32():g})'
        if t == 0x24: return f'byte({s.u8()})'
        if t == 0x25: return '0'
        if t == 0x26: return '1'
        if t == 0x27: return 'true'
        if t == 0x28: return 'false'
        if t == 0x29:
            k = s.u8()
            if k == 0: return 'text("")'
            if k == 1: src = s.expr(); s.expr(); s.expr(); return f'text({src})'
            if k in (2, 3): return f'text({s.expr()})'
            if k == 4: s.obj(); a = s.expr(); b = s.expr(); return f'strtable({a},{b})'
        if t == 0x2A: return 'None'
        if t == 0x2B: [s.f32() for _ in range(10)]; return 'transform'
        if t == 0x2C: return str(s.u8())
        if t == 0x2D: return 'NoInterface'
        if t == 0x2F: o = s.obj(); s.i32(); return f'struct<{o}>({", ".join(s.until(0x30))})'
        if t == 0x31: a = s.expr(); return f'setarray {a} = [{", ".join(s.until(0x32))}]'
        if t == 0x33: return f'prop({s.prop()})'
        if t == 0x34: return repr(s.wstr())
        if t in (0x35, 0x36): s.p += 8; s.mem += 8; return 'int64'
        if t == 0x38: k = s.u8(); return f'pcast{k}({s.expr()})'
        if t == 0x39: a = s.expr(); s.i32(); return f'setset {a} {s.until(0x3A)}'
        if t == 0x3B: a = s.expr(); s.i32(); return f'setmap {a} {s.until(0x3C)}'
        if t == 0x3D: s.prop(); s.i32(); return f'setconst {s.until(0x3E)}'
        if t == 0x3F: s.prop(); s.prop(); s.i32(); return f'mapconst {s.until(0x40)}'
        if t == 0x42: p = s.prop(); return f'{s.expr()}.{p}'
        if t == 0x4B: return f'delegate({s.name()})'
        if t == 0x4C: return f'push_flow @{s.u32()}'
        if t == 0x4D: return 'pop_flow'
        if t == 0x4E: return f'computed_jump {s.expr()}'
        if t == 0x4F: return f'pop_flow_if_not {s.expr()}'
        if t == 0x50: return 'breakpoint'
        if t == 0x51: return f'iface({s.expr()})'
        if t == 0x53: return 'END'
        if t in (0x5A, 0x5E): return 'tracepoint'
        if t == 0x5B: return f'skipconst {s.u32()}'
        if t in (0x5C, 0x62): a = s.expr(); return f'delegate_op {a} {s.expr()}'
        if t == 0x5D: return f'clear {s.expr()}'
        if t == 0x61: n = s.name(); a = s.expr(); return f'bind {n} {a} {s.expr()}'
        if t == 0x64: p = s.prop(); return f'letpersist {p} = {s.expr()}'
        if t == 0x65: p = s.prop(); s.i32(); return f'arrayconst {s.until(0x66)}'
        if t == 0x67: return f'softobj({s.expr()})'
        if t == 0x69:
            n = s.u16(); s.u32(); idx = s.expr(); cs = []
            for _ in range(n): v = s.expr(); s.u32(); cs.append(f'{v}:{s.expr()}')
            return f'switch {idx} {{{"; ".join(cs)}; default:{s.expr()}}}'
        if t == 0x6A:
            k = s.u8()
            if k == 4: s.name()
            return 'instr'
        if t == 0x6B: a = s.expr(); return f'{a}[{s.expr()}]'
        if t == 0x6D: return f'fieldpath({s.expr()})'
        raise ValueError(f'opcode desconhecido 0x{t:02x} em {s.p-1}')
    def run(s):
        while s.p < s.end:
            p, m = s.p, s.mem
            try: e = s.expr()
            except Exception as ex: s.out.append((p, m, f'!! {ex}')); break
            s.out.append((p, m, e))
            if e == 'END': break
        return s.out

def find_script(a, exp):
    lo, hi = exp['off'], exp['off'] + exp['size']
    d = a.d
    for q in range(hi - 9, lo - 1, -1):  # de tras para frente: o bytecode fica no fim do export
        mem, sz = struct.unpack_from('<ii', d, q)
        if 0 < sz and sz // 2 <= mem <= sz * 2 and 0 <= hi - (q + 8 + sz) <= 16 and d[q + 8 + sz - 1] == 0x53: return q + 8, q + 8 + sz
    return None
