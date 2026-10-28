# Edicao de bytecode Kismet com realocacao de saltos (alvos absolutos em offsets de memoria).
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kismet import Dis, find_script

class JumpScan(Dis):
    """Desmonta registrando (posicao_no_disco, valor) de cada operando de salto absoluto."""
    def __init__(s, *a, **k):
        super().__init__(*a, **k); s.targets = []
    def tgt(s):
        s.targets.append((s.p, struct.unpack_from('<I', s.d, s.p)[0])); return s.u32()
    def expr(s):
        t = s.d[s.p]
        if t in (0x06, 0x4C, 0x5B): s.u8(); return f'@{s.tgt()}'
        if t == 0x07: s.u8(); o = s.tgt(); return f'if {s.expr()} @{o}'
        if t == 0x18: s.u8(); s.tgt(); return f'skip {s.expr()}'
        if t == 0x69:
            s.u8(); n = s.u16(); s.tgt(); s.expr()
            for _ in range(n): s.expr(); s.tgt(); s.expr()
            s.expr(); return 'switch'
        return super().expr()

def edit_function(pkg, exp_idx, edits):
    """edits: lista de (pos_disco_absoluta_no_asset_original, bytes_novos, mem_novo).
    Cada edit substitui exatamente uma instrucao (statement) inteira."""
    a = pkg.a; e = a.exports[exp_idx]; s0, e0 = find_script(a, e)
    mem0, disk0 = struct.unpack_from('<ii', a.d, s0 - 8)
    dis = JumpScan(a, s0, e0); stmts = dis.run()
    bounds = {p: (m, (stmts[i + 1][0] if i + 1 < len(stmts) else e0), (stmts[i + 1][1] if i + 1 < len(stmts) else mem0))
              for i, (p, m, _) in enumerate(stmts)}
    blob = bytearray(pkg.blobs[exp_idx])  # pode ja conter patches de mesmo tamanho
    plan = []
    for pos, nb, nm in edits:
        m, pend, mend = bounds[pos]  # garante que pos e inicio de instrucao
        plan.append((pos, pend - pos, m, mend - m, nb, nm))
    # realoca alvos: cada edit em mem m (tamanho antigo om) muda o deslocamento de alvos > m
    def shift(v):
        d = 0
        for pos, od, m, om, nb, nm in plan:
            if v > m: d += nm - om
        return v + d
    for p, v in dis.targets:
        struct.pack_into('<I', blob, p - e['off'], shift(v))
    for pos, od, m, om, nb, nm in sorted(plan, reverse=True):
        r = pos - e['off']; blob[r:r + od] = nb
    dd = sum(len(nb) - od for pos, od, m, om, nb, nm in plan); dm = sum(nm - om for pos, od, m, om, nb, nm in plan)
    struct.pack_into('<ii', blob, s0 - 8 - e['off'], mem0 + dm, disk0 + dd)
    pkg.blobs[exp_idx] = bytes(blob)
    return dis
