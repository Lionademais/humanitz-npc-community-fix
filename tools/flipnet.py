# Marca propriedades de uma classe BP como replicadas (CPF_Net) e ajusta NumReplicatedProperties.
# Uso: flipnet.py origem.bin saida_dir NomeBase ClasseExport Prop:Tipo[:FuncRepNotify] [...]
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
src, outdir, base, cls = sys.argv[1:5]
p = Pkg(src); a = p.a
CLS = [i for i, e in enumerate(a.exports) if e['name'] == cls][0]
blob = bytearray(p.blobs[CLS]); I32 = lambda v: struct.pack('<i', v)
nrp = blob.find(I32(a.names.index('NumReplicatedProperties')) + I32(0))
assert nrp >= 0 and a.fn(*struct.unpack_from('<ii', blob, nrp + 8)) == 'IntProperty'
old = struct.unpack_from('<i', blob, nrp + 25)[0]; n = 0
for spec in sys.argv[5:]:
    nm, typ, *rn = spec.split(':')
    q = blob.find(I32(a.names.index(typ)) + I32(0) + I32(a.names.index(nm)) + I32(0)); assert q >= 0, spec
    f = struct.unpack_from('<Q', blob, q + 28)[0]; nf = f | 0x20
    if rn:  # CPF_RepNotify + nome da funcao chamada no cliente quando o valor chega
        nf |= 0x100000000; blob[q + 38:q + 46] = I32(a.names.index(rn[0])) + I32(0)
    if not f & 0x20: n += 1
    struct.pack_into('<Q', blob, q + 28, nf)
    print(f'{nm}: 0x{f:x} -> 0x{nf:x}' + (f' repnotify={rn[0]}' if rn else ''))
struct.pack_into('<i', blob, nrp + 25, old + n); p.blobs[CLS] = bytes(blob)
print(f'NumReplicatedProperties {old} -> {old + n}')
os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, base + '.uasset'), os.path.join(outdir, base + '.uexp'))
open(os.path.join(outdir, base + '.full'), 'wb').write(full)
