# UI_CommunityMemberInfo (cliente): para de recriar os tracos a cada atualizacao de 2 s da aba Comunidade.
# O jogo faz VBTraits.ClearChildren e cria de novo cada UI_TraitEntrySimple em todo UpdateInfo; o traco negativo
# (oculto) pisca e empurra o resto da ficha. Agora: logo depois de calcular ForceHidden, monta uma assinatura
# (UID do membro + ShouldRevealTraits + quantidade de tracos positivos/negativos); se for igual a do ultimo desenho
# (prop nova TraitsKey) e os tracos ainda estiverem la, pula a parte dos tracos (vai direto ao ramo seguinte).
# Uso: patch_traitui.py UI_CommunityMemberInfo.bin saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import Dis, find_script
from detour import Detour
from kasm import Asm

src, outdir = sys.argv[1:3]
p = Pkg(src); a = p.a
I32 = lambda v: struct.pack('<i', v); U32 = lambda v: struct.pack('<I', v)
FN = p.export_index('UpdateInfo') - 1; CLS = p.export_index('UI_CommunityMemberInfo_C') - 1
ENG, UMG, CORE = (p.find_import('Package', n) for n in ('/Script/Engine', '/Script/UMG', '/Script/CoreUObject'))
def cls(pkg, n): return p.find_import('Class', n, pkg) or p.add_import('/Script/CoreUObject', 'Class', pkg, n)
def fn(c, n): return p.add_import('/Script/CoreUObject', 'Function', c, n)
C_STR, C_GUID, C_ARR, C_MATH = cls(ENG, 'KismetStringLibrary'), cls(ENG, 'KismetGuidLibrary'), cls(ENG, 'KismetArrayLibrary'), cls(ENG, 'KismetMathLibrary')
C_PANEL = cls(UMG, 'PanelWidget')
F = {'Concat_StrStr': fn(C_STR, 'Concat_StrStr'), 'Conv_BoolToString': fn(C_STR, 'Conv_BoolToString'),
     'Conv_IntToString': fn(C_STR, 'Conv_IntToString'), 'EqualEqual_StrStr': fn(C_STR, 'EqualEqual_StrStr'),
     'Conv_GuidToString': fn(C_GUID, 'Conv_GuidToString'), 'Array_Length': fn(C_ARR, 'Array_Length'),
     'Less_IntInt': fn(C_MATH, 'Less_IntInt'), 'GetChildrenCount': fn(C_PANEL, 'GetChildrenCount')}
O_ARR = p.find_import('KismetArrayLibrary', 'Default__KismetArrayLibrary') or p.add_import('/Script/Engine', 'KismetArrayLibrary', ENG, 'Default__KismetArrayLibrary')
S_REC = p.find_import('ScriptStruct', 'NPCRecruitData'); assert S_REC

def cat(*parts): return b''.join(x[0] for x in parts), sum(x[1] for x in parts)
def op(c): return bytes([c]), 1
def path(n, owner): return I32(1) + I32(p.name(n)) + I32(0) + I32(owner), 8
NULLPATH = (I32(0) + I32(0), 8)
def inst(n): return cat(op(0x01), path(n, CLS + 1))
def local(n): return cat(op(0x00), path(n, FN + 1))
def objref(i): return I32(i), 8
def callmath(f, *x): return cat(op(0x68), objref(F[f]), *x, op(0x16))
def final(f, *x): return cat(op(0x1C), objref(F[f]), *x, op(0x16))
def context(obj, call): return cat(op(0x19), obj, (U32(call[1]), 4), NULLPATH, call)
def member(field, owner, expr): return cat(op(0x42), (I32(1) + I32(p.name(field)) + I32(0) + I32(owner), 8), expr)
def length(x): return context(cat(op(0x20), objref(O_ARR)), final('Array_Length', x))
def intc(v): return cat(op(0x1D), (I32(v), 4))
def cc(*xs):
    r = xs[0]
    for x in xs[1:]: r = callmath('Concat_StrStr', r, x)
    return r
D = inst('Data')
KEY = cc(callmath('Conv_GuidToString', member('UID', S_REC, D)), callmath('Conv_BoolToString', local('CallFunc_ShouldRevealTraits_ReturnValue')),
         callmath('Conv_IntToString', length(member('PositiveTraits', S_REC, D))),
         callmath('Conv_IntToString', length(member('NegativeTraits', S_REC, D))))

# ---- alvo: "let L:CallFunc_ShouldRevealTraits_ReturnValue = ..." (a origem de ForceHidden), seguido de Not_PreBool,
#      "let L:ForceHidden = ...", "push_flow @<ramo seguinte>" e "VBTraits.ClearChildren"
s0, e0 = find_script(a, a.exports[FN]); lines = Dis(a, s0, e0).run()
i = [k for k, (pos, m, x) in enumerate(lines) if x.startswith('let L:CallFunc_ShouldRevealTraits_ReturnValue = ')][0]
POS = lines[i][0]; assert 'Not_PreBool(L:CallFunc_ShouldRevealTraits_ReturnValue)' in lines[i + 1][2], lines[i + 1][2]
assert lines[i + 2][2].startswith('let L:ForceHidden = L:CallFunc_Not_PreBool'), lines[i + 2][2]
nxt = lines[i + 3][2]; assert nxt.startswith('push_flow @'), nxt
assert lines[i + 4][2] == 'I:VBTraits->ClearChildren()', lines[i + 4][2]
AFTER = int(nxt.split('@')[1])  # ramo seguinte da sequencia (estatisticas da ficha)

def extra(base):
    k = Asm(base)
    k.jnot('desenha', callmath('EqualEqual_StrStr', KEY, inst('TraitsKey')))
    k.jnot('desenha', callmath('Less_IntInt', intc(0), context(inst('VBTraits'), final('GetChildrenCount'))))
    k.st(cat(op(0x06), (U32(AFTER), 4)))  # mesmos tracos: pula a recriacao
    k.label('desenha')
    k.st(cat(op(0x0F), path('TraitsKey', CLS + 1), inst('TraitsKey'), KEY))
    code, mem, _ = k.build(); return code, mem
LOCALVAR = bytes(a.d[POS + 1:POS + 1 + 17]) if False else None
lv = cat(op(0x00), path('ForceHidden', FN + 1))[0]  # so para o preenchimento morto; assert len(lv) == 17
dt = Detour(p, FN); dt.detour(POS, extra, lv); dt.commit()

# ---- prop nova TraitsKey (StrProperty, transiente) no fim das propriedades da classe
blob = bytearray(p.blobs[CLS])
def key_of(name, typ): return I32(a.names.index(typ)) + I32(0) + I32(a.names.index(name)) + I32(0)
q_first = blob.find(key_of('BP_InvPRevWidget_NPC', 'ObjectProperty')); assert q_first > 0
cnt = struct.unpack_from('<i', blob, q_first - 4)[0]
q_data = blob.find(key_of('Data', 'StructProperty')); assert q_data > q_first
end_props = q_data + 47 + 4
OBJF = struct.unpack_from('<I', blob, q_data + 16)[0]
newprop = (I32(p.name('StrProperty')) + I32(0) + I32(p.name('TraitsKey')) + I32(0) + U32(OBJF) + I32(1) + I32(16)
           + struct.pack('<Q', 0x2000) + b'\0\0' + I32(p.name('None')) + I32(0) + b'\0')
blob[end_props:end_props] = newprop
struct.pack_into('<i', blob, q_first - 4, cnt + 1)
p.blobs[CLS] = bytes(blob)

os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'UI_CommunityMemberInfo.uasset'), os.path.join(outdir, 'UI_CommunityMemberInfo.uexp'))
open(os.path.join(outdir, 'UI_CommunityMemberInfo.full'), 'wb').write(full)
print(f'UI_CommunityMemberInfo: tracos so recriados quando mudam (pula para @{AFTER}); props {cnt}->{cnt + 1}', len(full))
