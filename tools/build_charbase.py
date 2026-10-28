# BP_CharacterBase (cliente): a roda de comandos dos seguidores chama SetNPCFollowCommand so no subsistema local.
# Desvia essa instrucao para tambem chamar OwningPlayerController.BP_HMZQuestComp.SRV_FollowNPC(NPC, Cmd, B1, B2).
# Uso: build_charbase.py origem.bin saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import Dis, find_script
from detour import Detour, relocated

src, outdir = sys.argv[1], sys.argv[2]
p = Pkg(src); a = p.a; d = a.d
UG = [i for i, e in enumerate(a.exports) if e['name'] == 'ExecuteUbergraph_BP_CharacterBase'][0]
# instrucoes localizadas pelo conteudo (o ubergraph muda de tamanho entre updates do jogo)
ST = Dis(a, *find_script(a, a.exports[UG])).run()
S = [q for q, m, t in ST if 'SetNPCFollowCommand' in t]  # L:Subsys->SetNPCFollowCommand(L:Recruit->I:NPCData, switch..., L:NotEqual, true)
assert len(S) == 1, S; S = S[0]                            # (OnOptionSelected_Event_1)
QSAMPLE = [q for q, m, t in ST if t.endswith('BP_HMZQuestComp->Update Quest Progress Items(true)') and d[q] == 0x19 and d[q + 1] == 0x19][0]

x = Dis(a, S, len(d)); assert x.u8() == 0x19
x.expr(); x.u32(); x.prop(); assert x.u8() == 0x1C; fn = x.obj(); assert fn.endswith('SetNPCFollowCommand'), fn
args = []
while d[x.p] != 0x16:
    p0, m0 = x.p, x.mem; x.expr(); args.append((p0, x.p, m0, x.mem - m0))
assert len(args) == 4
a0 = d[args[0][0]:args[0][1]]; assert a0[0] == 0x19 and a0[1] == 0x00
NPC = bytes(a0[1:18])                      # L:K2Node_DynamicCast_AsBP_Recruit_NPC
assert d[QSAMPLE] == 0x19 and d[QSAMPLE + 1] == 0x19
QCOMP = bytes(d[QSAMPLE + 1:QSAMPLE + 1 + 55]); QMEM = 31   # Context(I:OwningPlayerController)->I:BP_HMZQuestComp
C_QCOMP = p.find_import('BlueprintGeneratedClass', 'BP_HMZQuestComp_C'); assert C_QCOMP
F_RPC = p.add_import('/Script/CoreUObject', 'Function', C_QCOMP, 'SRV_FollowNPC')

dt = Detour(p, UG)
_, s_m0, _, targets = dt.stmt(S)
def extra(m_start):
    pre = 1 + QMEM + 4 + 8 + 1 + 8 + 9                     # ate o inicio do 2o argumento (switch)
    sw_old = s_m0 + args[1][2]; sw_new = m_start + pre
    sw = relocated(a, args[1][0], args[1][1], targets, sw_old, sw_new)
    call = b'\x1c' + struct.pack('<i', F_RPC) + NPC + sw + bytes(d[args[2][0]:args[2][1]]) + bytes(d[args[3][0]:args[3][1]]) + b'\x16'
    call_mem = 1 + 8 + 9 + args[1][3] + args[2][3] + args[3][3] + 1
    st = b'\x19' + QCOMP + struct.pack('<I', call_mem) + b'\0' * 8 + call
    return st, 1 + QMEM + 4 + 8 + call_mem
dt.detour(S, extra, NPC)
dt.commit()
sbs, cbs, sbc, cbc = p.deps[UG]; p.set_deps(UG, (sbs, cbs + [F_RPC], sbc, cbc))
os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'BP_CharacterBase.uasset'), os.path.join(outdir, 'BP_CharacterBase.uexp'))
open(os.path.join(outdir, 'BP_CharacterBase.full'), 'wb').write(full); print('ok', len(full))
