# UI_HMZQuest.CheckRecruit (cliente):
#  1) remove a trava HasAuthority (mesmo tamanho)
#  2) "pop_flow_if_not IsMemberInAnyCommunity" -> "if not IsMember jump @<bloco Recruit>":
#     membro (dados sincronizados) => <Manage>; nao membro => <Recruit>. (CanRecruit nativo e sempre falso no cliente)
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from reloc import edit_function
src, outdir = sys.argv[1], sys.argv[2]
p = Pkg(src); a = p.a
CR = [i for i, e in enumerate(a.exports) if e['name'] == 'CheckRecruit'][0]
blob = bytearray(p.blobs[CR]); off = a.exports[CR]['off']; d = a.d
# offsets relativos ao inicio do export da funcao (as funcoes alteradas nao mudam entre updates; so mudam de lugar)
def at(fn, rel): return [e for e in a.exports if e['name'] == fn][0]['off'] + rel
def CRO(rel): return at('CheckRecruit', rel)
LET = CRO(2907); RHS = LET + 1 + 17; END = CRO(2969)
assert d[LET] == 0x14 and d[RHS] == 0x19 and d[END] == 0x4F and d[END - 1] == 0x16
HA = struct.unpack_from('<i', d, END - 5)[0]; assert a.imports[-HA - 1][2] == 'HasAuthority'
local = bytes(d[LET + 1:RHS]); assert local[0] == 0x00 and len(local) == 17
new = b'\x27' + local + local + b'\x20' + struct.pack('<i', HA) + b'\x0b' * 4
assert len(new) == END - RHS == 44
blob[RHS - off:END - off] = new; p.blobs[CR] = bytes(blob)
POP = CRO(4636); RECRUIT = 298
assert d[POP] == 0x4F and d[POP + 1] == 0x00
ismember = bytes(d[POP + 1:POP + 18])
jn = b'\x07' + struct.pack('<I', RECRUIT) + ismember
from kismet import Dis, find_script
C_QCOMP = p.find_import('BlueprintGeneratedClass', 'BP_HMZQuestComp_C'); assert C_QCOMP
F_GETCOMP = p.find_import('Function', 'GetComponentByClass'); assert F_GETCOMP
SRV = {}
def parse_call(pos):
    x = Dis(a, pos, len(d)); assert x.u8() == 0x19
    o0, om = x.p, x.mem; x.expr(); obj = (bytes(d[o0:x.p]), x.mem - om)
    x.u32(); x.prop(); k = x.u8(); (x.obj() if k == 0x1C else x.name())
    args = []
    while d[x.p] != 0x16:
        a0, am = x.p, x.mem; x.expr(); args.append((bytes(d[a0:x.p]), x.mem - am))
    return k, obj, args
_, _, ref_args = parse_call(at('ConfirmTask', 1811)); UIDX = ref_args[0]  # I:Quest Dude->I:NPCData.UID
def cat(*parts): return b''.join(z[0] for z in parts), sum(z[1] for z in parts)
def op(c): return bytes([c]), 1
NULLP = (struct.pack('<ii', 0, 0), 8)
def final(fn, *args): return cat(op(0x1C), (struct.pack('<i', fn), 8), *args, op(0x16))
def context(obj, call): return cat(op(0x19), obj, (struct.pack('<I', call[1]), 4), NULLP, call)
OWNPC = (b'\x1b' + struct.pack('<ii', p.name('GetOwningPlayer'), 0) + b'\x16', 1 + 12 + 1)  # chamada virtual, como no original
QCOMP = context(OWNPC, final(F_GETCOMP, cat(op(0x20), (struct.pack('<i', C_QCOMP), 8))))
# 3) membro: preenche o NPCData do NPC no cliente com os dados sincronizados (lista de tarefas, traits etc.)
#    let I:Quest Dude->I:NPCData = Subsys->GetNPCDataByUID(I:Quest Dude->I:GUID, L:IsMember)
ISM, REQ, SET = CRO(4464), CRO(3424), CRO(4654)
im = bytes(d[ISM:ISM + 172]); assert im[0] == 0x14 and im[-1] == 0x16
subsys_local = im[19:36]; assert subsys_local[0] == 0x00
DUDE = b'\x19\x01' + struct.pack('<ii', 1, a.names.index('Quest Dude'))  # Context(I:Quest Dude ...)
dude_guid = im[im.index(DUDE):-1]; assert len(dude_guid) == 1 + 17 + 4 + 16 + 17
rq = bytes(d[REQ:REQ + 105]); k = rq.index(DUDE)
dude_npcdata = rq[k:k + 55]; assert dude_npcdata[-17] == 0x01
npcdata_path = dude_npcdata[22:38]
f_getnpc = p.add_import('/Script/CoreUObject', 'Function', p.find_import('Class', 'HZCommunityNPCSubSys'), 'GetNPCDataByUID')
call = b'\x1c' + struct.pack('<i', f_getnpc) + dude_guid + ismember + b'\x16'; call_mem = 9 + 31 + 9 + 1
rv = b'\x19' + subsys_local + struct.pack('<I', call_mem) + npcdata_path + call
mine = b'\x0f' + npcdata_path + dude_npcdata + rv; mine_mem = 1 + 8 + 31 + (1 + 9 + 4 + 8 + call_mem)
assert d[SET] == 0x14
orig = bytes(d[SET:SET + 19]); assert d[SET + 19] == 0x0f or True
#    e pede ao servidor os TSet/TMap do NPC (PossibleTasks, FollowCommands, Params), que a replicacao nao transporta
SRV['SRV_SyncNPC'] = p.add_import('/Script/CoreUObject', 'Function', C_QCOMP, 'SRV_SyncNPC')
dude = (bytes(dude_npcdata[1:18]), 9)  # I:Quest Dude
sync = context(QCOMP, final(SRV['SRV_SyncNPC'], dude, UIDX))
# 5) registra este dialogo em QComp.SyncUI (o CLIENT_NPCSync redesenha as traits quando os dados chegam); no ramo de
#    nao membro (opcao <Recruit>) tambem pede ao servidor o NPCData completo (GUID replicado do NPC). As traits e a
#    lista de tarefas ("o que voce sabe fazer") do HandleRecuit/HandleConfirmRecuit leem esse NPCData.
crst = Dis(a, *find_script(a, a.exports[CR])).run()
crnext = {crst[i][0]: (crst[i + 1][0], crst[i + 1][1] - crst[i][1]) for i in range(len(crst) - 1)}
SYNCUI = (struct.pack('<iii', 1, p.name('SyncUI'), 0) + struct.pack('<i', C_QCOMP), 8)
setui = cat(op(0x5F), context(QCOMP, cat(op(0x01), SYNCUI)), op(0x17))
sync_guid = context(QCOMP, final(SRV['SRV_SyncNPC'], dude, (dude_guid, 31)))
OPT_RECRUIT, ADD_MEMBER = CRO(3881), CRO(9215)  # criacao da opcao <Recruit> (nao membro); AddTraits() do ramo membro
extra = []
assert "text('<Recruit>')" in crst[[x[0] for x in crst].index(OPT_RECRUIT)][2]
assert crst[[x[0] for x in crst].index(ADD_MEMBER)][2] == 'AddTraits()'
for pos, pre in ((OPT_RECRUIT, [setui, sync_guid]), (ADD_MEMBER, [setui])):
    end, om = crnext[pos]
    extra.append((pos, b''.join(x[0] for x in pre) + bytes(d[pos:end]), sum(x[1] for x in pre) + om))
edit_function(p, CR, [(POP, jn, 1 + 4 + 9), (SET, mine + sync[0] + orig, mine_mem + sync[1] + 11)] + extra)
sbs, cbs, sbc, cbc = p.deps[CR]; p.set_deps(CR, (sbs, cbs + [SRV['SRV_SyncNPC']], sbc, cbc))
# 4) acoes de gerenciar: apos cada chamada local, repete via RPC no servidor (BP_HMZQuestComp.SRV_*)
from kismet import Dis, find_script
SITES = {  # funcao -> [(offset da instrucao relativo ao export, tipo)]
    'ConfirmTask': [(1811, 'SRV_AssignTask'), (2247, 'SRV_NPCHold'), (2325, 'SRV_NPCFriendly-'), (2597, 'SRV_ScheduleTask')],
    'ConfirmKick': [(407, 'SRV_AssignTask')],
    'CheckCampReturn': [(975, 'SRV_AssignTask')],
    'CheckTaggedTask': [(6915, 'SRV_ClearTask')],
    'HandleActions': [(23486, 'SRV_NPCFriendly+'), (23573, 'SRV_Follow'), (23698, 'SRV_ClearTask'), (23952, 'SRV_NPCHold'),
                      (24062, 'SRV_NPCFriendly-'), (24168, 'SRV_NPCFriendly-'), (24255, 'SRV_ClearTask'), (24587, 'SRV_NPCHold'), (24666, 'SRV_NPCHold')],
    'HandleRestCMD': [(1507, 'SRV_Sleep')],
    'Clear Forced Sleep': [(113, 'SRV_Sleep')],
    'OnContextOption': [(824, 'SRV_NPCEquip+'), (1253, 'SRV_NPCEquip-')],
}
for fname_, sites in SITES.items():
    ei = [i for i, e in enumerate(a.exports) if e['name'] == fname_][0]
    s0, e0 = find_script(a, a.exports[ei]); st = Dis(a, s0, e0).run()
    nxt = {st[i][0]: (st[i + 1][0], st[i + 1][1] - st[i][1]) for i in range(len(st) - 1)}
    edits = []
    for rel, kind in sites:
        pos = at(fname_, rel)
        rpc = kind.rstrip('+-')
        if rpc not in SRV: SRV[rpc] = p.add_import('/Script/CoreUObject', 'Function', C_QCOMP, rpc)
        k, obj, args = parse_call(pos)
        if rpc in ('SRV_AssignTask', 'SRV_ScheduleTask'): assert len(args) == 13; nargs = args[:9] + args[10:]
        elif rpc == 'SRV_ClearTask': assert len(args) == 4; nargs = args
        elif rpc == 'SRV_Follow': assert len(args) == 4; nargs = [UIDX] + args[1:]
        elif rpc == 'SRV_Sleep': assert len(args) == 2; nargs = [UIDX] + args[1:]
        elif rpc == 'SRV_NPCHold': assert k in (0x1B, 0x45) and len(args) == 2; nargs = [obj] + args
        elif rpc == 'SRV_NPCEquip' and kind.endswith('+'): assert len(args) == 1; nargs = [obj, args[0], op(0x28), op(0x28)]
        elif rpc == 'SRV_NPCEquip': assert len(args) == 2; nargs = [obj, args[0], op(0x27), args[1]]
        elif rpc == 'SRV_NPCFriendly': assert k in (0x1B, 0x45) and len(args) == 1; nargs = [obj, args[0], op(0x27 if kind.endswith('+') else 0x28)]
        new = context(QCOMP, final(SRV[rpc], *nargs))
        end, om = nxt[pos]; orig = bytes(d[pos:end])
        edits.append((pos, orig + new[0], om + new[1]))
    edit_function(p, ei, edits)
    sbs, cbs, sbc, cbc = p.deps[ei]
    p.set_deps(ei, (sbs, cbs + [x for x in SRV.values() if x not in cbs], sbc, cbc))
    print(f'{fname_}: {len(edits)} chamadas encaminhadas ao servidor')
os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'UI_HMZQuest.uasset'), os.path.join(outdir, 'UI_HMZQuest.uexp'))
open(os.path.join(outdir, 'UI_HMZQuest.full'), 'wb').write(full); print('ok', len(full))
