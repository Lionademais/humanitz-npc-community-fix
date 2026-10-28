# Desvio ("detour") de uma instrucao Kismet sem deslocar o resto da funcao:
#  - a instrucao original S vira: Jump <bloco> + instrucoes mortas (mesmo tamanho em disco e em memoria)
#  - no fim do script (antes do EX_EndOfScript) entra o bloco: S (com alvos absolutos realocados) + extras + Jump <apos S>
# Util quando a funcao (ex.: Ubergraph) tem pontos de entrada referenciados por offset em muitas outras funcoes.
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kismet import find_script
from reloc import JumpScan

def filler(disk, mem, localvar):
    """instrucoes mortas validas com exatamente (disk, mem) bytes; localvar = bytes de um EX_LocalVariable (17/9)"""
    diff = disk - mem; assert diff % 4 == 0 and len(localvar) == 17
    if diff >= 0: na = -(-diff // 8); nb = (8 * na - diff) // 4
    else: na, nb = 0, -diff // 4
    n = mem - 9 * na - 9 * nb; assert n >= 0, (disk, mem)
    out = localvar * na + (b'\x20' + struct.pack('<i', 0)) * nb + b'\x0b' * n
    assert len(out) == disk
    return out

def relocated(a, pos, end, targets, old_mem, new_mem):
    """bytes [pos, end) do asset com os alvos absolutos (offsets em memoria) deslocados de new_mem - old_mem"""
    b = bytearray(a.d[pos:end])
    for tp, v in targets:
        if pos <= tp < end: struct.pack_into('<I', b, tp - pos, v + (new_mem - old_mem))
    return bytes(b)

class Detour:
    def __init__(s, pkg, exp_idx):
        s.p, s.i = pkg, exp_idx; a = pkg.a; s.a = a
        e = a.exports[exp_idx]; s.e = e; s.s0, s.e0 = find_script(a, e)
        s.mem0, s.disk0 = struct.unpack_from('<ii', a.d, s.s0 - 8)
        assert a.d[s.e0 - 1] == 0x53
        s.end_mem = s.mem0 - 1  # onde o bloco novo comeca (no lugar do EX_EndOfScript)
        s.blob = bytearray(pkg.blobs[exp_idx]); s.tail = b''; s.tail_mem = 0
    def stmt(s, pos):
        """(fim_no_disco, mem_inicio, mem_tamanho, alvos) de uma instrucao que comeca em pos (disco)"""
        x = JumpScan(s.a, s.s0, s.e0)
        while x.p < pos: x.expr()
        assert x.p == pos, 'pos nao e inicio de instrucao'
        m0 = x.mem; x.targets = []; x.expr()
        return x.p, m0, x.mem - m0, list(x.targets)
    def detour(s, pos, extra_builder, localvar):
        """extra_builder(new_mem_of_block_after_S) -> (bytes, mem) com instrucoes a executar depois de S"""
        end, m0, msz, tg = s.stmt(pos); dsz = end - pos
        blk_mem = s.end_mem + s.tail_mem
        s_copy = relocated(s.a, pos, end, tg, m0, blk_mem)
        extra = extra_builder(blk_mem + msz)
        back = b'\x06' + struct.pack('<I', m0 + msz)
        block = s_copy + extra[0] + back; bmem = msz + extra[1] + 5
        jump = b'\x06' + struct.pack('<I', blk_mem)
        rep = jump + filler(dsz - 5, msz - 5, localvar)
        r = pos - s.e['off']; s.blob[r:r + dsz] = rep
        s.tail += block; s.tail_mem += bmem
    def commit(s):
        r_end = s.e0 - s.e['off']
        s.blob[r_end - 1:r_end - 1] = s.tail
        struct.pack_into('<ii', s.blob, s.s0 - 8 - s.e['off'], s.mem0 + s.tail_mem, s.disk0 + len(s.tail))
        s.p.blobs[s.i] = bytes(s.blob)
