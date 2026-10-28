# BP_GameStateBase.HandleNPCRecruits: nao pular a criacao dos recrutaveis em servidor dedicado
import sys, struct, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset import Asset
src, outdir = sys.argv[1], sys.argv[2]
a = Asset(src); end = max(e['off'] + e['size'] for e in a.exports) + 4; d = bytearray(a.d[:end])
J = 613890; assert d[J] == 0x07 and struct.unpack_from('<I', d, J + 1)[0] == 1702
struct.pack_into('<I', d, J + 1, 201)
os.makedirs(outdir, exist_ok=True)
open(os.path.join(outdir, 'BP_GameStateBase.uasset'), 'wb').write(d[:a.header_size])
open(os.path.join(outdir, 'BP_GameStateBase.uexp'), 'wb').write(d[a.header_size:])
open(os.path.join(outdir, 'BP_GameStateBase.full'), 'wb').write(d)
print('patch ok')
