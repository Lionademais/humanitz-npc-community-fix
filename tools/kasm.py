# Montador minimo de bytecode Kismet com rotulos (offsets de salto em memoria, absolutos a partir de 'base').
# Expressoes sao tuplas (bytes_em_disco, tamanho_em_memoria).
import struct

class Asm:
    def __init__(s, base):
        s.base, s.items = base, []
    def st(s, expr): s.items.append(('s', expr))
    def label(s, name): s.items.append(('l', name))
    def jmp(s, name): s.items.append(('j', name, None))
    def jnot(s, name, cond): s.items.append(('j', name, cond))
    def _size(s, it):
        if it[0] == 's': return it[1][1]
        if it[0] == 'l': return 0
        return 5 + (it[2][1] if it[2] else 0)
    def build(s):
        labels, off = {}, s.base
        for it in s.items:
            if it[0] == 'l': labels[it[1]] = off
            off += s._size(it)
        out, mem = bytearray(), 0
        for it in s.items:
            if it[0] == 's': out += it[1][0]; mem += it[1][1]
            elif it[0] == 'j':
                tgt = struct.pack('<I', labels[it[1]])
                if it[2] is None: out += b'\x06' + tgt; mem += 5
                else: out += b'\x07' + tgt + it[2][0]; mem += 5 + it[2][1]
        return bytes(out), mem, labels
