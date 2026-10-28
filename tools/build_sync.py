# BP_HMZQuestComp: sincroniza os dados de comunidade servidor -> cliente.
#  - replica CommunityList e PlayerUID (CPF_Net)
#  - nova propriedade replicada CommSync (FNPCCommunityDataArray) + mapa auxiliar CommSyncMap
#  - TSet/TMap nao sao replicados pelo UE: o servidor achata os Params das comunidades e os PossibleTasks,
#    FollowCommands e Params de cada membro em arrays replicados (Sync*); o cliente os reconstroi em CommSync
#  - laco a cada 2 s iniciado no BeginPlay:
#      servidor: CommSyncMap = Subsys.GetWorldCommunityData(); Map_Find(CommSyncMap, PlayerUID, CommSync); achata TSet/TMap
#      cliente:  SetDTList; reconstroi TSet/TMap; Map_Clear/Map_Add(CommSyncMap, PlayerUID, CommSync); Subsys.SetCommunityData
#  - --server: depois de achatar, esvazia todos os TMap da copia CommSync (comunidade, membro, acoes, tarefas, inventario,
#    traits). Mapa que muda faz o UE logar "Replicated TMaps are not supported" a cada envio; o cliente nunca recebia
#    esses mapas mesmo. So usa variaveis ja existentes: o layout continua identico ao do cliente.
#    Antes, recria comunidades de bases orfas (construidas ou upgradadas sem o subsistema) do jogador e iguala o nivel,
#    e avisa o jogador por popup quando recriou alguma.
# Uso: build_sync.py origem.bin saida_dir [--server]
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import find_script
from kasm import Asm

src, outdir = sys.argv[1], sys.argv[2]
SERVER = '--server' in sys.argv[3:]
p = Pkg(src); a = p.a
I32 = lambda v: struct.pack('<i', v)
U32 = lambda v: struct.pack('<I', v)

def exp_idx(name):
    return [i for i, e in enumerate(a.exports) if e['name'] == name][0]
UG, RBP, CLS = exp_idx('ExecuteUbergraph_BP_HMZQuestComp'), exp_idx('ReceiveBeginPlay'), exp_idx('BP_HMZQuestComp_C')

def imp(cls, name):
    r = p.find_import(cls, name); assert r, (cls, name); return r
def fname(n, num=0): return I32(p.name(n)) + I32(num)
def split_num(n):  # 'Foo_6' -> ('Foo', 7) como FName com numero
    base, _, tail = n.rpartition('_')
    if tail.isdigit() and base: return base, int(tail) + 1
    return n, 0

# ---- imports
SUBSYS = imp('Class', 'HZCommunityNPCSubSys'); MAPLIB = imp('Class', 'BlueprintMapLibrary')
TSS, ENGPKG = imp('Package', '/Script/TSSGame'), imp('Package', '/Script/Engine')
F_GETWORLD = p.add_import('/Script/CoreUObject', 'Function', SUBSYS, 'GetWorldCommunityData')
F_SETDATA = p.add_import('/Script/CoreUObject', 'Function', SUBSYS, 'SetCommunityData')
F_GETOWNER, F_HASAUTH = imp('Function', 'GetOwner'), imp('Function', 'HasAuthority')
F_GETSUBSYS, F_DELAY = imp('Function', 'GetWorldSubsystem'), imp('Function', 'Delay')
O_MAPLIB = imp('BlueprintMapLibrary', 'Default__BlueprintMapLibrary')
O_ARRLIB = imp('KismetArrayLibrary', 'Default__KismetArrayLibrary')
C_ARRLIB, C_MATHLIB = imp('Class', 'KismetArrayLibrary'), imp('Class', 'KismetMathLibrary')
C_SETLIB = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'BlueprintSetLibrary')
O_SETLIB = p.add_import('/Script/Engine', 'BlueprintSetLibrary', ENGPKG, 'Default__BlueprintSetLibrary')
S_LATENT = imp('ScriptStruct', 'LatentActionInfo')
S_DATAARR = p.add_import('/Script/CoreUObject', 'ScriptStruct', TSS, 'NPCCommunityDataArray')
S_COMM = p.add_import('/Script/CoreUObject', 'ScriptStruct', TSS, 'NPCCommunityData')
S_REC = imp('ScriptStruct', 'NPCRecruitData')
C_USERWIDGET = p.add_import('/Script/CoreUObject', 'Class', imp('Package', '/Script/UMG'), 'UserWidget')
F_SETDT = p.add_import('/Script/CoreUObject', 'Function', SUBSYS, 'SetDTList')
F = {}
for n in ('Map_Add', 'Map_Find', 'Map_Clear', 'Map_Keys', 'Map_Values'): F[n] = p.add_import('/Script/CoreUObject', 'Function', MAPLIB, n)
for n in ('Array_Clear', 'Array_Append', 'Array_Add', 'Array_Length'): F[n] = p.add_import('/Script/CoreUObject', 'Function', C_ARRLIB, n)
for n in ('Set_ToArray', 'Set_Clear', 'Set_Add'): F[n] = p.add_import('/Script/CoreUObject', 'Function', C_SETLIB, n)
for n in ('Less_IntInt', 'Add_IntInt', 'EqualEqual_IntInt'): F[n] = p.add_import('/Script/CoreUObject', 'Function', C_MATHLIB, n)
if SERVER:
    S_ACTION, S_DECAY, S_INV, S_TRAIT = (p.add_import('/Script/CoreUObject', 'ScriptStruct', TSS, n)
                                         for n in ('NPCActionInfo', 'NPCStatDecayConfig', 'NPCInventoryItem', 'NPCTraitInfo'))
    for n in ('GetCommunityLevel', 'AddNewCommunity', 'UpgradeBase'): F[n] = p.add_import('/Script/CoreUObject', 'Function', SUBSYS, n)
    F['IsValid'], F['IsValid_Guid'] = imp('Function', 'IsValid'), imp('Function', 'IsValid_Guid')
    F['EqualEqual_GuidGuid'] = p.add_import('/Script/CoreUObject', 'Function', imp('Class', 'KismetGuidLibrary'), 'EqualEqual_GuidGuid')
    F['GetGameState'] = imp('Function', 'GetGameState')
    F['GetTransform'] = p.add_import('/Script/CoreUObject', 'Function', imp('Class', 'Actor'), 'GetTransform')
    C_CTRL = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'Controller')
    F['K2_GetPawn'] = p.add_import('/Script/CoreUObject', 'Function', C_CTRL, 'K2_GetPawn')
    # titulo = chave que o cliente (patch_showmsg.py) troca pela lingua do jogo; cliente antigo mostra em ingles
    NEW_NAME = '(Rename your community)'
    F['Conv_StringToText'] = p.add_import('/Script/CoreUObject', 'Function', imp('Class', 'KismetTextLibrary'), 'Conv_StringToText')
    MSG_TITLE = 'Community restored'
    MSG_TEXT = ("Your base had no community: it was built or upgraded while the server's community fix was inactive "
                '(usually right after a game or mod update). The community has been recreated, but the survivors who were '
                'in it could not be recovered. Rename the community at the base. This will not happen again in future updates.')
    C_GS, C_BIA = imp('BlueprintGeneratedClass', 'BP_GameStateBase_C'), imp('BlueprintGeneratedClass', 'BP_BaseInteractActor_C')
    BASEDIR = '/Game/TSS_Game/KaiWorldEffects/InteractActor/Child/BPK_CommunityBaseLevel'
    C_LV = {n: p.add_import('/Script/Engine', 'BlueprintGeneratedClass',
                            p.add_import('/Script/CoreUObject', 'Package', 0, f'{BASEDIR}{n}'), f'BPK_CommunityBaseLevel{n}_C')
            for n in (1, 2, 3, 4)}
DTDIR = '/Game/TSS_Game/KaiAIMapTest/KaiHumanAI/Quest/QuestPreset/Random/Recruit/Data/'
DTS = []
for dt in ('DT_NPC_Responses', 'DT_Recruit_PositiveTraits', 'DT_Recruit_NegativeTraits'):
    pk = p.add_import('/Script/CoreUObject', 'Package', 0, DTDIR + dt)
    DTS.append(p.add_import('/Script/Engine', 'DataTable', pk, dt))

# ---- bytecode helpers (disco); devolvem (bytes, tamanho_em_memoria)
def path(prop, owner):
    n, num = split_num(prop) if owner == UG + 1 else (prop, 0)
    return I32(1) + fname(n, num) + I32(owner), 8
NULLPATH = (I32(0) + I32(0), 8)
def cat(*parts):
    b = b''.join(x[0] for x in parts); m = sum(x[1] for x in parts); return b, m
def op(c): return bytes([c]), 1
def local(n): return cat(op(0x00), path(n, UG + 1))
def inst(n): return cat(op(0x01), path(n, CLS + 1))
def objref(i): return I32(i), 8
def final(fn, *args): return cat(op(0x1C), objref(fn), *args, op(0x16))
def callmath(fn, *args): return cat(op(0x68), objref(fn), *args, op(0x16))
def context(obj, call, rv=NULLPATH): return cat(op(0x19), obj, (U32(call[1]), 4), rv, call)
def objconst(i): return cat(op(0x20), objref(i))
def member(field, owner, expr): return cat(op(0x42), (I32(1) + fname(field) + I32(owner), 8), expr)
def aref(arr, idx): return cat(op(0x6B), arr, idx)
def intc(v): return cat(op(0x1D), (I32(v), 4))
def lib(obj, fn, *args): return context(objconst(obj), final(F[fn], *args))
def arr(fn, *args): return lib(O_ARRLIB, fn, *args)
def mapl(fn, *args): return lib(O_MAPLIB, fn, *args)
def setl(fn, *args): return lib(O_SETLIB, fn, *args)
def math(fn, *args): return callmath(F[fn], *args)
def length(x): return arr('Array_Length', x)
def letv(name, rhs): return cat(op(0x0F), path(name, CLS + 1), inst(name), rhs)
def inc(name): return letv(name, math('Add_IntInt', inst(name), intc(1)))
SELF = op(0x17)

ug = a.exports[UG]; s0, e0 = find_script(a, ug)
mem0, disk0 = struct.unpack_from('<ii', a.d, s0 - 8)
B = mem0 - 1  # offset (memoria) do novo bloco: onde hoje fica o EX_EndOfScript do ubergraph
assert a.d[e0 - 1] == 0x53 and a.d[e0 - 3:e0 - 1] == b'\x04\x0b'

L_OWNER, L_AUTH, L_SUB = 'CallFunc_GetOwner_ReturnValue_6', 'CallFunc_HasAuthority_ReturnValue', 'CallFunc_GetWorldSubsystem_ReturnValue_1'
COMMS = member('Communities', S_DATAARR, inst('CommSync'))
def comm(i): return aref(COMMS, i)
def mems(i): return member('Members', S_COMM, comm(i))
def mem_(i, j): return aref(mems(i), j)
REPL = [('SyncCPKeys', 'namearr'), ('SyncCPVals', 'floatarr'), ('SyncCPCount', 'intarr'), ('SyncMTasks', 'bytearr'), ('SyncMTCount', 'intarr'),
        ('SyncMFollow', 'bytearr'), ('SyncMFCount', 'intarr'), ('SyncMPKeys', 'namearr'), ('SyncMPVals', 'floatarr'), ('SyncMPCount', 'intarr')]
TEMPS = [(n, 'int') for n in ('SyncI', 'SyncJ', 'SyncK', 'SyncG', 'SyncCC', 'SyncCT', 'SyncCF', 'SyncCP')] + \
        [('SyncTmpBytes', 'bytearr'), ('SyncTmpKeys', 'namearr'), ('SyncTmpVals', 'floatarr'), ('SyncMsgW', 'widget')]
# SyncMsgW: janela do aviso de comunidade restaurada (so cliente, patch_showmsg.py); existe dos dois lados p/ layout igual

k = Asm(B)
k.st(cat(op(0x5F), local(L_OWNER), final(F_GETOWNER)))
k.st(cat(op(0x14), local(L_AUTH), context(local(L_OWNER), final(F_HASAUTH), path(L_AUTH, UG + 1))))
k.st(cat(op(0x5F), local(L_SUB), callmath(F_GETSUBSYS, SELF, objconst(SUBSYS))))
k.jnot('client', local(L_AUTH))
# ---------------- servidor
if SERVER:
    # Base orfa: construida/upgradada sem o subsistema (passo 2 fora), o GUID entrou na CommunityList mas a comunidade
    # nao existe (ou ficou com nivel menor). Para cada GUID da lista com base no mundo: cria a comunidade e iguala o nivel.
    # GetCommunityLevel devolve 0 se nao existe; AddNewCommunity cria no nivel 1; UpgradeBase soma 1.
    def ivar(n, owner): return cat(op(0x01), path(n, owner))
    def field(obj, n, owner): return context(obj, ivar(n, owner), path(n, owner))
    def dcast(cls, x): return cat(op(0x2E), objref(cls), x)
    def isobj(x): return cat(op(0x38), op(0x47), x)
    def sub(fn, *args): return context(local(L_SUB), final(F[fn], *args))
    def ustr(t):
        try: return cat(op(0x1F), (t.encode('ascii') + b'\0', len(t) + 1))
        except UnicodeEncodeError: b = t.encode('utf-16-le') + b'\0\0'; return cat(op(0x34), (b, len(b)))
    GS = dcast(C_GS, callmath(F['GetGameState'], SELF))
    BASES = field(GS, 'CommunityBaseList', C_GS)
    BX = aref(BASES, inst('SyncJ'))
    G = aref(inst('CommunityList'), inst('SyncI'))
    SPAWNS = field(BX, 'SpawnLocList', C_LV[1])
    LEVEL = sub('GetCommunityLevel', inst('PlayerUID'), G)
    k.jnot('h_end', callmath(F['IsValid'], local(L_SUB)))
    k.jnot('h_end', callmath(F['IsValid_Guid'], inst('PlayerUID')))
    k.st(letv('SyncI', intc(0)))
    k.label('h_ci'); k.jnot('h_end', math('Less_IntInt', inst('SyncI'), length(inst('CommunityList'))))
    k.st(letv('SyncJ', intc(0)))
    k.label('h_bj'); k.jnot('h_next', math('Less_IntInt', inst('SyncJ'), length(BASES)))
    k.jnot('h_bnext', isobj(dcast(C_LV[1], BX)))
    k.jnot('h_bnext', callmath(F['EqualEqual_GuidGuid'], field(BX, 'GUID', C_BIA), G))
    k.st(letv('SyncK', intc(1)))
    for n in (2, 3, 4):
        k.jnot(f'h_lv{n}', isobj(dcast(C_LV[n], BX))); k.st(letv('SyncK', intc(n))); k.label(f'h_lv{n}')
    k.jnot('h_up', math('Less_IntInt', LEVEL, intc(1)))
    k.jnot('h_up', sub('AddNewCommunity', inst('PlayerUID'), G, ustr(NEW_NAME), context(BX, final(F['GetTransform'])), SPAWNS))
    # nome tambem na base (ActorName replicado, ver flipnet): senao a placa fica "Unknown Community" ate reiniciar
    k.st(cat(op(0x0F), path('ActorName', C_BIA), field(BX, 'ActorName', C_BIA), callmath(F['Conv_StringToText'], ustr(NEW_NAME))))
    k.st(letv('SyncG', intc(1)))  # recriou: agenda o aviso
    k.label('h_up'); k.jnot('h_next', math('Less_IntInt', LEVEL, inst('SyncK')))
    k.jnot('h_next', math('Less_IntInt', intc(0), LEVEL))
    k.st(sub('UpgradeBase', inst('PlayerUID'), G, SPAWNS)); k.jmp('h_up')
    k.label('h_bnext'); k.st(inc('SyncJ')); k.jmp('h_bj')
    k.label('h_next'); k.st(inc('SyncI')); k.jmp('h_ci')
    k.label('h_end')
    # Aviso ao jogador (CLIENT_ShowQuestMessage -> popup de missao, ja existe no cliente). SyncG so e usado no cliente;
    # aqui conta os ciclos com o personagem no mundo para a HUD existir. RPC nao confiavel: envia duas vezes.
    PAWN = context(dcast(C_CTRL, local(L_OWNER)), final(F['K2_GetPawn']))
    MSG = final(exp_idx('CLIENT_ShowQuestMessage') + 1, ustr(MSG_TITLE), ustr(MSG_TEXT))
    k.jnot('m_end', math('Less_IntInt', intc(0), inst('SyncG')))
    k.jnot('m_end', callmath(F['IsValid'], PAWN))
    k.st(inc('SyncG'))
    k.jnot('m_2', math('EqualEqual_IntInt', inst('SyncG'), intc(6))); k.st(MSG)
    k.label('m_2'); k.jnot('m_end', math('EqualEqual_IntInt', inst('SyncG'), intc(9))); k.st(MSG); k.st(letv('SyncG', intc(0)))
    k.label('m_end')
k.st(cat(op(0x0F), path('CommSyncMap', CLS + 1), inst('CommSyncMap'), context(local(L_SUB), final(F_GETWORLD), path('CommSyncMap', CLS + 1))))
k.st(mapl('Map_Find', inst('CommSyncMap'), inst('PlayerUID'), inst('CommSync')))
for n, _ in REPL: k.st(arr('Array_Clear', inst(n)))
k.st(letv('SyncI', intc(0)))
k.label('s_ci'); k.jnot('s_ci_end', math('Less_IntInt', inst('SyncI'), length(COMMS)))
P = member('Params', S_COMM, comm(inst('SyncI')))
k.st(mapl('Map_Keys', P, inst('SyncTmpKeys'))); k.st(mapl('Map_Values', P, inst('SyncTmpVals')))
k.st(arr('Array_Append', inst('SyncCPKeys'), inst('SyncTmpKeys'))); k.st(arr('Array_Append', inst('SyncCPVals'), inst('SyncTmpVals')))
k.st(arr('Array_Add', inst('SyncCPCount'), length(inst('SyncTmpKeys'))))
k.st(letv('SyncJ', intc(0)))
k.label('s_mj'); k.jnot('s_mj_end', math('Less_IntInt', inst('SyncJ'), length(mems(inst('SyncI')))))
M = mem_(inst('SyncI'), inst('SyncJ'))
for field, dst, cnt in (('PossibleTasks', 'SyncMTasks', 'SyncMTCount'), ('FollowCommands', 'SyncMFollow', 'SyncMFCount')):
    k.st(setl('Set_ToArray', member(field, S_REC, M), inst('SyncTmpBytes')))
    k.st(arr('Array_Append', inst(dst), inst('SyncTmpBytes'))); k.st(arr('Array_Add', inst(cnt), length(inst('SyncTmpBytes'))))
MP = member('Params', S_REC, M)
k.st(mapl('Map_Keys', MP, inst('SyncTmpKeys'))); k.st(mapl('Map_Values', MP, inst('SyncTmpVals')))
k.st(arr('Array_Append', inst('SyncMPKeys'), inst('SyncTmpKeys'))); k.st(arr('Array_Append', inst('SyncMPVals'), inst('SyncTmpVals')))
k.st(arr('Array_Add', inst('SyncMPCount'), length(inst('SyncTmpKeys'))))
if SERVER:
    def clear(m): k.st(mapl('Map_Clear', m))
    def each(arr_expr, lb, body):  # for SyncK in arr_expr: body(elemento)
        k.st(letv('SyncK', intc(0)))
        k.label(lb); k.jnot(lb + '_end', math('Less_IntInt', inst('SyncK'), length(arr_expr)))
        body(aref(arr_expr, inst('SyncK')))
        k.st(inc('SyncK')); k.jmp(lb); k.label(lb + '_end')
    def action(x):
        for f in ('FExtra', 'SExtra', 'StatEffects_PerSec'): clear(member(f, S_ACTION, x))
    for f in ('StatusEffects', 'Params', 'TempParams'): clear(member(f, S_REC, M))
    clear(member('StatDecays', S_DECAY, member('StatDecayConfig', S_REC, M)))
    action(member('CurrentAction', S_REC, M)); action(member('PreSleepAction', S_REC, M))
    each(member('AssignedTasks', S_REC, M), 's_at', action)
    each(member('Inventory', S_REC, M), 's_inv', lambda x: [clear(member(f, S_INV, x)) for f in ('SExtra', 'FExtra')])
    for f in ('PositiveTraits', 'NegativeTraits'):
        each(member(f, S_REC, M), 's_' + f, lambda x: clear(member('Effects', S_TRAIT, x)))
k.st(inc('SyncJ')); k.jmp('s_mj'); k.label('s_mj_end')
if SERVER: k.st(mapl('Map_Clear', member('Params', S_COMM, comm(inst('SyncI')))))
k.st(inc('SyncI')); k.jmp('s_ci'); k.label('s_ci_end')
k.jmp('delay')
# ---------------- cliente
k.label('client')
k.st(context(local(L_SUB), final(F_SETDT, *[objconst(x) for x in DTS])))  # tabelas de falas/traits (dialogos)
k.jnot('c_done', math('EqualEqual_IntInt', length(inst('SyncCPCount')), length(COMMS)))
for n in ('SyncI', 'SyncG', 'SyncCC', 'SyncCT', 'SyncCF', 'SyncCP'): k.st(letv(n, intc(0)))
k.label('c_ci'); k.jnot('c_done', math('Less_IntInt', inst('SyncI'), length(COMMS)))
P = member('Params', S_COMM, comm(inst('SyncI')))
k.st(mapl('Map_Clear', P)); k.st(letv('SyncK', intc(0)))
k.label('c_ck'); k.jnot('c_ck_end', math('Less_IntInt', inst('SyncK'), aref(inst('SyncCPCount'), inst('SyncI'))))
k.jnot('c_ck_end', math('Less_IntInt', inst('SyncCC'), length(inst('SyncCPKeys'))))
k.st(mapl('Map_Add', P, aref(inst('SyncCPKeys'), inst('SyncCC')), aref(inst('SyncCPVals'), inst('SyncCC'))))
k.st(inc('SyncK')); k.st(inc('SyncCC')); k.jmp('c_ck'); k.label('c_ck_end')
k.st(letv('SyncJ', intc(0)))
k.label('c_mj'); k.jnot('c_mj_end', math('Less_IntInt', inst('SyncJ'), length(mems(inst('SyncI')))))
k.jnot('c_mj_end', math('Less_IntInt', inst('SyncG'), length(inst('SyncMTCount'))))
M = mem_(inst('SyncI'), inst('SyncJ'))
for field, src_, cnt, cur in (('PossibleTasks', 'SyncMTasks', 'SyncMTCount', 'SyncCT'), ('FollowCommands', 'SyncMFollow', 'SyncMFCount', 'SyncCF')):
    S = member(field, S_REC, M); lb = 'c_' + field
    k.st(setl('Set_Clear', S)); k.st(letv('SyncK', intc(0)))
    k.label(lb); k.jnot(lb + '_end', math('Less_IntInt', inst('SyncK'), aref(inst(cnt), inst('SyncG'))))
    k.jnot(lb + '_end', math('Less_IntInt', inst(cur), length(inst(src_))))
    k.st(setl('Set_Add', S, aref(inst(src_), inst(cur))))
    k.st(inc('SyncK')); k.st(inc(cur)); k.jmp(lb); k.label(lb + '_end')
MP = member('Params', S_REC, M)
k.st(mapl('Map_Clear', MP)); k.st(letv('SyncK', intc(0)))
k.label('c_mp'); k.jnot('c_mp_end', math('Less_IntInt', inst('SyncK'), aref(inst('SyncMPCount'), inst('SyncG'))))
k.jnot('c_mp_end', math('Less_IntInt', inst('SyncCP'), length(inst('SyncMPKeys'))))
k.st(mapl('Map_Add', MP, aref(inst('SyncMPKeys'), inst('SyncCP')), aref(inst('SyncMPVals'), inst('SyncCP'))))
k.st(inc('SyncK')); k.st(inc('SyncCP')); k.jmp('c_mp'); k.label('c_mp_end')
k.st(inc('SyncJ')); k.st(inc('SyncG')); k.jmp('c_mj'); k.label('c_mj_end')
k.st(inc('SyncI')); k.jmp('c_ci')
k.label('c_done')
k.st(mapl('Map_Clear', inst('CommSyncMap')))
k.st(mapl('Map_Add', inst('CommSyncMap'), inst('PlayerUID'), inst('CommSync')))
k.st(context(local(L_SUB), final(F_SETDATA, inst('CommSyncMap'))))
# ---------------- espera 2 s e repete
k.label('delay')
latent = cat(op(0x2F), objref(S_LATENT), (I32(0x20), 4), cat(op(0x5B), (U32(B), 4)),
             cat(op(0x1D), (I32(0x7C5E1A2B), 4)), cat(op(0x21), (fname('ExecuteUbergraph_BP_HMZQuestComp'), 12)), SELF, op(0x30))
k.st(callmath(F_DELAY, SELF, cat(op(0x1E), (struct.pack('<f', 2.0), 4)), latent))
k.st(op(0x4D))
code, cmem, labels = k.build()
print(f'bloco: disco {len(code)} memoria {cmem}  client@{labels["client"]} delay@{labels["delay"]}')

blob = bytearray(p.blobs[UG]); rs = s0 - ug['off']; re_ = e0 - ug['off']
blob[re_ - 1:re_ - 1] = code
struct.pack_into('<ii', blob, rs - 8, mem0 + cmem, disk0 + len(code))
p.blobs[UG] = bytes(blob)
sbs, cbs, sbc, cbc = p.deps[UG]
NEWDEPS = DTS + ([C_LV[n] for n in (1, 2, 3, 4)] if SERVER else [])
p.set_deps(UG, (sbs, cbs + [x for x in NEWDEPS if x not in cbs], sbc, cbc))

# ---- ReceiveBeginPlay: chama tambem ExecuteUbergraph(B)
rb = a.exports[RBP]; s1, e1 = find_script(a, rb); m1, k1 = struct.unpack_from('<ii', a.d, s1 - 8)
call = cat(op(0x46), objref(UG + 1), cat(op(0x1D), (I32(B), 4)), op(0x16))
blob = bytearray(p.blobs[RBP]); rs = s1 - rb['off']; re_ = e1 - rb['off']
assert blob[re_ - 3:re_] == b'\x04\x0b\x53'
blob[re_ - 3:re_ - 3] = call[0]
struct.pack_into('<ii', blob, rs - 8, m1 + call[1], k1 + len(call[0]))
p.blobs[RBP] = bytes(blob)

# ---- classe: flags de rede, NumReplicatedProperties, novas propriedades
cl = a.exports[CLS]; blob = bytearray(p.blobs[CLS])
def find_prop(name, typ):
    key = I32(a.names.index(typ)) + I32(0) + I32(a.names.index(name)) + I32(0)
    q = blob.find(key); assert q >= 0, name; return q
nrp = blob.find(I32(a.names.index('NumReplicatedProperties')) + I32(0)); assert nrp >= 0
assert a.fn(*struct.unpack_from('<ii', blob, nrp + 8)) == 'IntProperty'
old = struct.unpack_from('<i', blob, nrp + 25)[0]
for nm, typ in (('CommunityList', 'ArrayProperty'), ('PlayerUID', 'StructProperty')):
    q = find_prop(nm, typ); f = struct.unpack_from('<Q', blob, q + 28)[0]; struct.pack_into('<Q', blob, q + 28, f | 0x20)
q_uber = find_prop('UberGraphFrame', 'StructProperty'); cnt = struct.unpack_from('<i', blob, q_uber - 4)[0]
q_last = find_prop('DoneRadioTower?', 'BoolProperty'); end_props = q_last + 47 + 6
q_pu = find_prop('PlayerUID', 'StructProperty'); OBJF = struct.unpack_from('<I', blob, q_pu + 16)[0]
def fprop(fclass, name, pflags, esize, extra=b''):
    return fname(fclass) + fname(name) + U32(OBJF) + I32(1) + I32(esize) + struct.pack('<Q', pflags) + b'\0\0' + fname('None') + b'\0' + extra
def typed(name, t, pflags):
    if t == 'int': return fprop('IntProperty', name, pflags, 4)
    if t == 'bytearr': return fprop('ArrayProperty', name, pflags, 16) + fprop('ByteProperty', name, 0, 1, I32(0))
    if t == 'namearr': return fprop('ArrayProperty', name, pflags, 16) + fprop('NameProperty', name, 0, 12)
    if t == 'floatarr': return fprop('ArrayProperty', name, pflags, 16) + fprop('FloatProperty', name, 0, 4)
    if t == 'intarr': return fprop('ArrayProperty', name, pflags, 16) + fprop('IntProperty', name, 0, 4)
    if t == 'widget': return fprop('ObjectProperty', name, pflags, 8, I32(C_USERWIDGET))
    raise ValueError(t)
newprops = fprop('StructProperty', 'CommSync', 0x10025, 16, I32(S_DATAARR))
newprops += fprop('MapProperty', 'CommSyncMap', 0x10005, 80) + fprop('StructProperty', 'CommSyncMap', 0, 16, I32(imp('ScriptStruct', 'Guid'))) \
            + fprop('StructProperty', 'CommSyncMap_Value', 0, 16, I32(S_DATAARR))
newprops += b''.join(typed(n, t, 0x10025) for n, t in REPL) + b''.join(typed(n, t, 0x10005) for n, t in TEMPS)
nnew = 2 + len(REPL) + len(TEMPS)
blob[end_props:end_props] = newprops
struct.pack_into('<i', blob, q_uber - 4, cnt + nnew)
struct.pack_into('<i', blob, nrp + 25, old + 3 + len(REPL))  # CommunityList, PlayerUID, CommSync + arrays Sync*
p.blobs[CLS] = bytes(blob)
print(f'props {cnt}->{cnt + nnew}, NumReplicatedProperties {old}->{old + 3 + len(REPL)}')

os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'BP_HMZQuestComp.uasset'), os.path.join(outdir, 'BP_HMZQuestComp.uexp'))
open(os.path.join(outdir, 'BP_HMZQuestComp.full'), 'wb').write(full)
print('ok', len(full))
