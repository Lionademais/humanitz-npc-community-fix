# BPK_CommunityBaseLevel1 (servidor): ao renomear (OnServerButtonPress), logo apos Subsys.SetCommunityName chama
# FlushNetDormancy + ForceNetUpdate (o ActorName e gravado em seguida, no mesmo frame, antes da replicacao). A Base e uma construcao dormente na rede: sem isso o nome novo so chega
# aos clientes quando eles reentram no servidor.
# Uso: patch_basename.py entrada.full saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import Dis, find_script
from detour import Detour

src, outdir = sys.argv[1], sys.argv[2]
p = Pkg(src); a = p.a; d = a.d
UG = [i for i, e in enumerate(a.exports) if e['name'] == 'ExecuteUbergraph_BPK_CommunityBaseLevel1'][0]
st = Dis(a, *find_script(a, a.exports[UG])).run()
S = [pos for pos, m, t in st if 'HZCommunityNPCSubSys.SetCommunityName(' in t]
assert len(S) == 1, S
S = S[0]; assert d[S] == 0x19 and d[S + 1] == 0x00
lv = bytes(d[S + 1:S + 18])  # L:<subsistema> (para o preenchimento)
C_ACTOR = p.find_import('Class', 'Actor'); assert C_ACTOR
F = [p.add_import('/Script/CoreUObject', 'Function', C_ACTOR, n) for n in ('FlushNetDormancy', 'ForceNetUpdate')]
calls = b''.join(b'\x1c' + struct.pack('<i', f) + b'\x16' for f in F)
dt = Detour(p, UG)
dt.detour(S, lambda m: (calls, 10 * len(F)), lv)
dt.commit()
os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'BPK_CommunityBaseLevel1.uasset'), os.path.join(outdir, 'BPK_CommunityBaseLevel1.uexp'))
open(os.path.join(outdir, 'BPK_CommunityBaseLevel1.full'), 'wb').write(full); print('Base (nome) ok', len(full))
