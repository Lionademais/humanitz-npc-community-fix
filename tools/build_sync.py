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
for n in ('Less_IntInt', 'Add_IntInt', 'EqualEqual_IntInt', 'Subtract_IntInt', 'Greater_IntInt'): F[n] = p.add_import('/Script/CoreUObject', 'Function', C_MATHLIB, n)
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
if not SERVER:
    C_STRLIB = p.find_import('Class', 'KismetStringLibrary') or p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'KismetStringLibrary')
    C_TXTLIB = p.find_import('Class', 'KismetTextLibrary') or p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'KismetTextLibrary')
    for n in ('FindSubstring', 'Left', 'RightChop', 'Concat_StrStr', 'StartsWith', 'EndsWith', 'Mid', 'Len', 'Replace', 'EqualEqual_StrStr'):
        F[n] = p.add_import('/Script/CoreUObject', 'Function', C_STRLIB, n)
    C_I18N = p.find_import('Class', 'KismetInternationalizationLibrary') or p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'KismetInternationalizationLibrary')
    F['GetCurrentCulture'] = p.add_import('/Script/CoreUObject', 'Function', C_I18N, 'GetCurrentCulture')
    for n in ('FindTextInLocalizationTable', 'Conv_TextToString'): F[n] = p.add_import('/Script/CoreUObject', 'Function', C_TXTLIB, n)
    F['Array_Set'] = p.add_import('/Script/CoreUObject', 'Function', C_ARRLIB, 'Array_Set')
    F['Map_Length'] = p.add_import('/Script/CoreUObject', 'Function', MAPLIB, 'Map_Length')
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
        [('SyncTmpBytes', 'bytearr'), ('SyncTmpKeys', 'namearr'), ('SyncTmpVals', 'floatarr'), ('SyncMsgW', 'widget'),
         ('SyncStr', 'str'), ('SyncTxt', 'text'), ('SyncTrMap', 'strmap'),
         ('SyncStrP', 'str'), ('SyncStrB', 'str'), ('SyncStrX', 'str'), ('SyncStrC', 'str'),
         ('SyncTrBack', 'strmap'), ('SyncStrO', 'str'), ('SyncStrL', 'str')]
# SyncStr/SyncTxt/SyncTrMap: traducao das falas (ChatHistory) no cliente; existem dos dois lados p/ layout igual
# SyncTrBack (linha traduzida -> linha original em ingles) / SyncStrO: a traducao e gravada na copia replicada do cliente;
# para trocar de idioma em jogo, cada linha volta ao ingles antes de traduzir de novo. SyncStrL: idioma da ultima passada;
# no mesmo idioma, linhas ja traduzidas sao puladas (so as novas passam pela traducao)
# SyncMsgW: janela do aviso de comunidade restaurada (so cliente, patch_showmsg.py); existe dos dois lados p/ layout igual

TRMAP, TEMPLATES = [], []
if not SERVER:
    # Tabela de traducao do historico (SyncTrMap): "ingles" -> chave oficial (DT_NPC_Responses, DT_TaskConfig, via locres
    # ingles) e "<lingua>|ingles" -> traducao propria (tools/chat_translations.py). TEMPLATES: modelos com {X}.
    import re as _re
    from locres import read as _read_locres
    from chat_translations import OWN, ALIASES, NESTED
    _root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'originais')
    _en = _read_locres(os.path.join(_root, 'locres', 'Game_en.locres'))
    _seen, _official = set(), {}
    for _dtf in ('DT_NPC_Responses_srv.bin', 'DT_TaskConfig_srv.bin'):
        _dt = open(os.path.join(_root, _dtf), 'rb').read()
        for _m in _re.finditer(rb'\x21\x00\x00\x00([0-9A-F]{32})\x00', _dt):
            _q = _m.end(); _n = struct.unpack_from('<i', _dt, _q)[0]; _q += 4
            _src = _dt[_q:_q - 2 * _n].decode('utf-16-le').rstrip('\0') if _n < 0 else _dt[_q:_q + _n].decode('latin1').rstrip('\0')
            _key = _m.group(1).decode()
            for _txt in (_src, _en.get(('', _key))):  # texto do asset e o exibido em ingles (o servidor usa o exibido)
                if _txt and _txt not in _seen: _seen.add(_txt); _official[_txt] = _key; TRMAP.append((_txt, _key))
    # textos que os blueprints dos NPCs escrevem direto no historico (originais/historico/*.bin): chave -> ingles exibido
    for _bf in sorted(os.listdir(os.path.join(_root, 'historico'))):
        _bd = open(os.path.join(_root, 'historico', _bf), 'rb').read()
        for _key in sorted({_m.group(1).decode() for _m in _re.finditer(rb'([0-9A-F]{32})\x00', _bd)}):
            _txt = _en.get(('', _key))
            if _txt and _txt not in _seen: _seen.add(_txt); _official[_txt] = _key; TRMAP.append((_txt, _key))
    for _a, _b in ALIASES.items(): TRMAP.append((_a, _official[_b]))
    for _en_t, _tr in OWN.items():
        for _lang, _t in _tr.items(): TRMAP.append((f'{_lang}|{_en_t}', _t))
    for _t in sorted({t for t in list(_official) + list(ALIASES) + list(OWN) if '{X}' in t}, key=lambda t: (-len(t), t)):  # ordem fixa
        _a, _, _b = _t.partition('{X}'); TEMPLATES.append((_a, _b, _t, _t in NESTED))
    print(f'traducao do historico: {len(TRMAP)} entradas, {len(TEMPLATES)} modelos com nome')

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
if not SERVER:
    # Historico (ChatHistory): o servidor grava as linhas ja em ingles ("<PR>[NPC]</>: fala",
    # "<PR>[Tarefa]</>-<SP>[NPC]</>: fala",
    # "X has died."...). A cada 2 s cada linha e traduzida para a lingua do jogo antes de ir ao subsistema:
    # nome da tarefa e falas pela traducao oficial (chave + FindTextInLocalizationTable), modelos com {X} (nome no meio)
    # e frases fixas do C++ pelas traducoes proprias. Linhas ja traduzidas ou desconhecidas ficam como estao.
    def ustr_(t):
        try: return cat(op(0x1F), (t.encode('ascii') + b'\0', len(t) + 1))
        except UnicodeEncodeError: b = t.encode('utf-16-le') + b'\0\0'; return cat(op(0x34), (b, len(b)))
    def sfn(n, *a): return callmath(F[n], *a)
    def bytec(v): return cat(op(0x24), (bytes([v]), 1))
    TR, R, P, Bd, X, CP = (inst(n) for n in ('SyncTrMap', 'SyncStr', 'SyncStrP', 'SyncStrB', 'SyncStrX', 'SyncStrC'))
    def setstr(n, rhs): return letv(n, rhs)
    lab = [0]
    def lookup(src, ok):  # R = traducao de src (propria da lingua ou oficial); pula para ok se achou
        lab[0] += 1; nxt = f'lk{lab[0]}'
        k.jnot(nxt, mapl('Map_Find', TR, sfn('Concat_StrStr', CP, src), R)); k.jmp(ok)
        k.label(nxt); nxt2 = f'lk{lab[0]}b'
        k.jnot(nxt2, mapl('Map_Find', TR, src, R))
        k.jnot(nxt2, sfn('FindTextInLocalizationTable', ustr_(''), R, inst('SyncTxt')))
        k.st(setstr('SyncStr', sfn('Conv_TextToString', inst('SyncTxt')))); k.jmp(ok)
        k.label(nxt2)
    k.jnot('tr_ok', math('EqualEqual_IntInt', mapl('Map_Length', TR), intc(0)))
    for a_, b_ in TRMAP: k.st(mapl('Map_Add', TR, ustr_(a_), ustr_(b_)))
    k.label('tr_ok')
    k.st(setstr('SyncStrC', sfn('Concat_StrStr', sfn('Left', sfn('GetCurrentCulture'), intc(2)), ustr_('|'))))
    k.st(letv('SyncI', intc(0)))
    k.label('t_ci'); k.jnot('t_end', math('Less_IntInt', inst('SyncI'), length(COMMS)))
    k.st(letv('SyncJ', intc(0)))
    k.label('t_mj'); k.jnot('t_mj_end', math('Less_IntInt', inst('SyncJ'), length(mems(inst('SyncI')))))
    CH = member('ChatHistory', S_REC, mem_(inst('SyncI'), inst('SyncJ')))
    E = aref(CH, inst('SyncK'))
    k.st(letv('SyncK', intc(0)))
    k.label('t_k'); k.jnot('t_k_end', math('Less_IntInt', inst('SyncK'), length(CH)))
    # linha ja traduzida: no mesmo idioma, pula; se o idioma mudou, volta ao original em ingles e traduz de novo
    k.jnot('t_orig', mapl('Map_Find', inst('SyncTrBack'), E, R))
    k.jnot('t_volta', sfn('EqualEqual_StrStr', inst('SyncStrL'), CP))
    k.jmp('t_prox')
    k.label('t_volta'); k.st(arr('Array_Set', CH, inst('SyncK'), R, op(0x28)))
    k.label('t_orig'); k.st(setstr('SyncStrO', E))
    # prefixo "[..]: " e corpo
    k.st(letv('SyncCT', sfn('FindSubstring', E, ustr_('</>: '), op(0x28), op(0x28), intc(-1))))
    k.st(setstr('SyncStrP', ustr_(''))); k.st(setstr('SyncStrB', E))
    k.jnot('t_pre', math('Less_IntInt', intc(-1), inst('SyncCT')))
    CUT = math('Add_IntInt', inst('SyncCT'), intc(5))
    k.st(setstr('SyncStrP', sfn('Left', E, CUT))); k.st(setstr('SyncStrB', sfn('RightChop', E, CUT)))
    # nome da tarefa em "[Tarefa]-[NPC]: "
    k.st(letv('SyncCF', sfn('FindSubstring', P, ustr_(']</>-<SP>['), op(0x28), op(0x28), intc(-1))))
    k.jnot('t_pre', math('Greater_IntInt', inst('SyncCF'), intc(5)))
    k.jnot('t_pre', sfn('StartsWith', P, ustr_('<PR>['), bytec(0)))
    lookup(sfn('Mid', P, intc(5), math('Subtract_IntInt', inst('SyncCF'), intc(5))), 't_task')
    k.jmp('t_pre')
    k.label('t_task'); k.st(setstr('SyncStrP', sfn('Concat_StrStr', sfn('Concat_StrStr', ustr_('<PR>['), R), sfn('RightChop', P, inst('SyncCF')))))
    k.label('t_pre')
    # corpo: frase exata
    lookup(Bd, 't_exact')
    # modelos com {X}
    LEN = sfn('Len', Bd)
    for ti, (a_, b_, t_, nested) in enumerate(TEMPLATES):
        nx = f't_m{ti}'
        if a_: k.jnot(nx, sfn('StartsWith', Bd, ustr_(a_), bytec(0)))
        if b_: k.jnot(nx, sfn('EndsWith', Bd, ustr_(b_), bytec(0)))
        k.jnot(nx, math('Less_IntInt', intc(len(a_) + len(b_)), LEN))
        k.st(setstr('SyncStrX', sfn('Mid', Bd, intc(len(a_)), math('Subtract_IntInt', LEN, intc(len(a_) + len(b_))))))
        if nested:
            lookup(X, f't_n{ti}'); k.jmp(f't_nd{ti}')
            k.label(f't_n{ti}'); k.st(setstr('SyncStrX', R)); k.label(f't_nd{ti}')
        lookup(ustr_(t_), f't_ok{ti}'); k.jmp(nx)
        k.label(f't_ok{ti}'); k.st(setstr('SyncStrB', sfn('Replace', R, ustr_('{X}'), X, bytec(0)))); k.jmp('t_set')
        k.label(nx)
    k.jmp('t_set')
    k.label('t_exact'); k.st(setstr('SyncStrB', R))
    k.label('t_set')
    k.st(arr('Array_Set', CH, inst('SyncK'), sfn('Concat_StrStr', P, Bd), op(0x28)))
    k.st(mapl('Map_Add', inst('SyncTrBack'), E, inst('SyncStrO')))
    k.label('t_prox'); k.st(inc('SyncK')); k.jmp('t_k')
    k.label('t_k_end'); k.st(inc('SyncJ')); k.jmp('t_mj')
    k.label('t_mj_end'); k.st(inc('SyncI')); k.jmp('t_ci')
    k.label('t_end'); k.st(setstr('SyncStrL', CP))
    if os.environ.get('HZ_DIAG_TRAITS'):
        # DIAGNOSTICO (pak de teste apenas): 1a linha do historico de cada membro vira o estado que o cliente tem
        for n in ('Conv_IntToString', 'Conv_BoolToString', 'Conv_FloatToString'): F[n] = p.add_import('/Script/CoreUObject', 'Function', C_STRLIB, n)
        F['ShouldRevealTraits'] = p.add_import('/Script/CoreUObject', 'Function', SUBSYS, 'ShouldRevealTraits')
        F['GetTimeSeconds'] = p.add_import('/Script/CoreUObject', 'Function', imp('Class', 'GameplayStatics'), 'GetTimeSeconds')
        def cc(*xs):
            r = xs[0]
            for x in xs[1:]: r = sfn('Concat_StrStr', r, x)
            return r
        k.st(letv('SyncI', intc(0)))
        k.label('d_ci'); k.jnot('d_end', math('Less_IntInt', inst('SyncI'), length(COMMS)))
        k.st(letv('SyncJ', intc(0)))
        k.label('d_mj'); k.jnot('d_mj_end', math('Less_IntInt', inst('SyncJ'), length(mems(inst('SyncI')))))
        M_ = mem_(inst('SyncI'), inst('SyncJ')); CH_ = member('ChatHistory', S_REC, M_)
        REV = context(local(L_SUB), final(F['ShouldRevealTraits'], M_, cat(op(0x1E), (struct.pack('<f', 3.0), 4))))
        LINE = cc(ustr_('<PR>[DBG]</>: NT='), sfn('Conv_IntToString', length(member('NegativeTraits', S_REC, M_))),
                  ustr_(' PT='), sfn('Conv_IntToString', length(member('PositiveTraits', S_REC, M_))),
                  ustr_(' P='), sfn('Conv_IntToString', mapl('Map_Length', member('Params', S_REC, M_))),
                  ustr_(' REV='), sfn('Conv_BoolToString', REV),
                  ustr_(' t='), sfn('Conv_FloatToString', callmath(F['GetTimeSeconds'], op(0x17))))
        k.jnot('d_add', math('Less_IntInt', intc(0), length(CH_)))
        k.st(arr('Array_Set', CH_, intc(0), LINE, op(0x28))); k.jmp('d_next')
        k.label('d_add'); k.st(arr('Array_Add', CH_, LINE))
        k.label('d_next'); k.st(inc('SyncJ')); k.jmp('d_mj')
        k.label('d_mj_end'); k.st(inc('SyncI')); k.jmp('d_ci')
        k.label('d_end')
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
    if t == 'str': return fprop('StrProperty', name, pflags, 16)
    if t == 'text': return fprop('TextProperty', name, pflags, 24)
    if t == 'strmap': return fprop('MapProperty', name, pflags, 80) + fprop('StrProperty', name, 0, 16) + fprop('StrProperty', name + '_Value', 0, 16)
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
