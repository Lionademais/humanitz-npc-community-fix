# C-Building.CheckBuildingCollision (servidor): neutraliza o teste IsLocalController que marcava "Comm?" para quem
# nao e host (Base da Comunidade so construivel pelo host). JumpIfNot @706 -> @570.
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
src, outdir = sys.argv[1], sys.argv[2]
p = Pkg(src); a = p.a; d = a.d
POS = 189114; assert d[POS] == 0x07 and struct.unpack_from('<I', d, POS + 1)[0] == 706
i = [k for k, e in enumerate(a.exports) if e['off'] <= POS < e['off'] + e['size']][0]
blob = bytearray(p.blobs[i]); struct.pack_into('<I', blob, POS + 1 - a.exports[i]['off'], 570); p.blobs[i] = bytes(blob)
os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'C-Building.uasset'), os.path.join(outdir, 'C-Building.uexp'))
open(os.path.join(outdir, 'C-Building.full'), 'wb').write(full); print('ok', len(full))
