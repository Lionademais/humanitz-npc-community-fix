# BPK_CommunityBaseLevel1 (cliente): no BeginPlay nao sobrescreve o ActorName (replicado do servidor) com o nome
# do subsistema local, que ainda esta vazio e devolve "Unknown Community". pop_flow_if_not X -> pop_flow; X (mesmo tamanho)
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
src, outdir = sys.argv[1], sys.argv[2]
p = Pkg(src); a = p.a; d = a.d
UG = [i for i, e in enumerate(a.exports) if e['name'] == 'ExecuteUbergraph_BPK_CommunityBaseLevel1'][0]
POS = int(sys.argv[3]); assert d[POS] == 0x4F and d[POS + 1] == 0x00
blob = bytearray(p.blobs[UG]); r = POS - a.exports[UG]['off']
blob[r] = 0x4D  # pop_flow; a variavel local que vinha como condicao vira uma instrucao morta (17 bytes, valida)
p.blobs[UG] = bytes(blob)
os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'BPK_CommunityBaseLevel1.uasset'), os.path.join(outdir, 'BPK_CommunityBaseLevel1.uexp'))
open(os.path.join(outdir, 'BPK_CommunityBaseLevel1.full'), 'wb').write(full); print('ok', len(full))
