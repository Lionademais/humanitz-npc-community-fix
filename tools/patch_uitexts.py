# Traduz os textos da aba Comunidade que o jogo deixa em ingles (cliente):
#  - rotulos fixos do designer gravados como texto "invariante" (ex.: "Community Stats", "Current Task:", "Danger Lv:"):
#    na primeira execucao do ponto de entrada do widget, le a cultura (Left(GetCurrentCulture(), 2)) e faz
#    TextBlock_N.SetText(<traducao propria>) — ui_translations.LABELS / T. Ingles: nada muda.
#  - UI_CommunityMemberInfo: horarios da agenda (strings 'Morning'... fixas) passam a usar a traducao oficial do jogo
#    (texto localizado com a chave do Game.locres); "Status", "N/A" e "Status: N/A" (chaves sem traducao em pt/de) usam a propria.
#  - cabe no espaco: mede no jogo (ForceLayoutPrepass + GetDesiredSize) o texto em ingles e a traducao no mesmo TextBlock e, se a
#    traducao passar de ui_translations.FIT x ingles, reduz a escala de renderizacao dela (SetRenderScale). WRAP: quebra de linha.
#  - UI_CommunityMember (linha do membro): "Morale" ao lado do nome.
# Props novas (transientes) no fim da classe: UiLang (guarda/idioma), UiStatus, UiNA (Str); UiW, UiH, UiE (Float, medida).
# Uso: patch_uitexts.py entrada(.bin|.full) saida_dir NomeDoAsset
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import Dis, find_script
from detour import Detour
from kasm import Asm
import locres
from ui_translations import T, LANGS, LABELS, SCHEDULE, FIT, WRAP

src, outdir, NAME = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
p = Pkg(src); a = p.a
I32 = lambda v: struct.pack('<i', v); U32 = lambda v: struct.pack('<I', v)
CLS = p.export_index(NAME + '_C') - 1
ENG, UMG = p.find_import('Package', '/Script/Engine'), p.find_import('Package', '/Script/UMG')
def cls(pkg, n): return p.find_import('Class', n, pkg) or p.add_import('/Script/CoreUObject', 'Class', pkg, n)
def fn(c, n): return p.add_import('/Script/CoreUObject', 'Function', c, n)
C_STR, C_TXT, C_I18N = cls(ENG, 'KismetStringLibrary'), cls(ENG, 'KismetTextLibrary'), cls(ENG, 'KismetInternationalizationLibrary')
C_TB, C_W, C_MATH = cls(UMG, 'TextBlock'), cls(UMG, 'Widget'), cls(ENG, 'KismetMathLibrary')
F = {'Concat_StrStr': fn(C_STR, 'Concat_StrStr'), 'Left': fn(C_STR, 'Left'), 'EqualEqual_StrStr': fn(C_STR, 'EqualEqual_StrStr'),
     'NotEqual_StrStr': fn(C_STR, 'NotEqual_StrStr'),
     'Conv_StringToText': fn(C_TXT, 'Conv_StringToText'), 'Conv_TextToString': fn(C_TXT, 'Conv_TextToString'),
     'GetCurrentCulture': fn(C_I18N, 'GetCurrentCulture'), 'SetText': fn(C_TB, 'SetText'),
     'ForceLayoutPrepass': fn(C_W, 'ForceLayoutPrepass'), 'GetDesiredSize': fn(C_W, 'GetDesiredSize'),
     'SetRenderScale': fn(C_W, 'SetRenderScale'), 'BreakVector2D': fn(C_MATH, 'BreakVector2D'),
     'MakeVector2D': fn(C_MATH, 'MakeVector2D'), 'Divide_FloatFloat': fn(C_MATH, 'Divide_FloatFloat'),
     'Greater_FloatFloat': fn(C_MATH, 'Greater_FloatFloat'), 'Multiply_FloatFloat': fn(C_MATH, 'Multiply_FloatFloat')}

def cat(*parts): return b''.join(x[0] for x in parts), sum(x[1] for x in parts)
def op(c): return bytes([c]), 1
def split_num(n):  # 'TextBlock_7' -> ('TextBlock', 8): FName com numero, como o cooker grava
    base, _, tail = n.rpartition('_')
    if n not in a.names and base and tail.isdigit() and (tail == '0' or tail[0] != '0'): return base, int(tail) + 1
    return n, 0
def fname(n): b, num = split_num(n); return I32(p.name(b)) + I32(num)
def path(n, owner): return I32(1) + fname(n) + I32(owner), 8
NULLPATH = (I32(0) + I32(0), 8)
def inst(n): return cat(op(0x01), path(n, CLS + 1))
def objref(i): return I32(i), 8
def callmath(f, *x): return cat(op(0x68), objref(F[f]), *x, op(0x16))
def final(f, *x): return cat(op(0x1C), objref(F[f]), *x, op(0x16))
def context(obj, call): return cat(op(0x19), obj, (U32(call[1]), 4), NULLPATH, call)
def intc(v): return cat(op(0x1D), (I32(v), 4))
def floatc(v): return cat(op(0x1E), (struct.pack('<f', v), 4))
def ustr(t):
    try: return cat(op(0x1F), (t.encode('ascii') + b'\0', len(t) + 1))
    except UnicodeEncodeError: b = t.encode('utf-16-le') + b'\0\0'; return cat(op(0x34), (b, len(b)))
def textconst(src_, key, ns=''): return cat(op(0x29), op(0x01), ustr(src_), ustr(key), ustr(ns))  # texto localizado
def settext(tb, s): return context(inst(tb), final('SetText', callmath('Conv_StringToText', s)))
def letinst(n, v): return cat(op(0x0F), path(n, CLS + 1), inst(n), v)
def stmts(fn_idx):
    s0, e0 = find_script(a, a.exports[fn_idx]); return Dis(a, s0, e0).run()
def find(lines, pred, what):
    r = [pos for pos, m, x in lines if pred(x)]; assert len(r) == 1, (what, r); return r[0]

PROPS = ['UiLang', 'UiFitLang'] + (['UiStatus', 'UiNA'] if NAME == 'UI_CommunityMemberInfo' else [])
FPROPS = ['UiW', 'UiH', 'UiE']  # largura/altura medidas e limite (FloatProperty)
for lang in LANGS:
    for eng in list(LABELS[NAME].values()) + ['Status', 'N/A']: assert T[eng].get(lang), (eng, lang)
assert set(FIT[NAME]) <= set(LABELS[NAME]) and not set(FIT[NAME]) & set(WRAP.get(NAME, [])), NAME

def lang_block(k):
    """quando o idioma do jogo muda (ou na 1a vez): UiLang = cultura; rotulos traduzidos (ou de volta ao ingles, com escala 1);
    UiStatus/UiNA no idioma. Roda a cada atualizacao do widget, mas so faz algo se o idioma mudou."""
    CUR = callmath('Left', callmath('GetCurrentCulture'), intc(2))
    k.jnot('fim_idioma', callmath('NotEqual_StrStr', inst('UiLang'), CUR))
    k.st(letinst('UiLang', CUR))
    for lang in LANGS:
        k.jnot('nao_' + lang, callmath('EqualEqual_StrStr', inst('UiLang'), ustr(lang)))
        for tb, eng in sorted(LABELS[NAME].items()): k.st(settext(tb, ustr(T[eng][lang])))
        if 'UiStatus' in PROPS:
            k.st(letinst('UiStatus', ustr(T['Status'][lang]))); k.st(letinst('UiNA', ustr(T['N/A'][lang])))
        k.jmp('fim_idioma')
        k.label('nao_' + lang)
    # ingles / idioma sem traducao propria: textos originais e escala normal
    for tb, eng in sorted(LABELS[NAME].items()): k.st(settext(tb, ustr(eng)))
    for tb in sorted(FIT[NAME]): k.st(context(inst(tb), final('SetRenderScale', callmath('MakeVector2D', floatc(1.0), floatc(1.0)))))
    if 'UiStatus' in PROPS:
        k.st(letinst('UiStatus', ustr('Status'))); k.st(letinst('UiNA', ustr('N/A')))
    k.label('fim_idioma')
def fit_block(k):
    """cabe no espaco: para cada rotulo de FIT, mede (prepass do Slate) o texto em ingles e a traducao no mesmo TextBlock;
    se a traducao passar de fator x ingles, reduz a escala de renderizacao dela na proporcao. Sem efeito enquanto o Slate do
    widget nao existe (largura 0)."""
    def width(tb, s_):
        k.st(settext(tb, s_)); k.st(context(inst(tb), final('ForceLayoutPrepass')))
        k.st(callmath('BreakVector2D', context(inst(tb), final('GetDesiredSize')), inst('UiW'), inst('UiH')))
    # so depois de trocar de idioma (UiFitLang != UiLang) e ate conseguir medir uma vez (Slate pronto: largura > 0)
    k.jnot('fim_mede', callmath('NotEqual_StrStr', inst('UiFitLang'), inst('UiLang')))
    for lang in LANGS:
        k.jnot('nao_mede_' + lang, callmath('EqualEqual_StrStr', inst('UiLang'), ustr(lang)))
        for tb, fat in sorted(FIT[NAME].items()):
            eng = LABELS[NAME][tb]
            width(tb, ustr(eng)); k.st(letinst('UiE', callmath('Multiply_FloatFloat', inst('UiW'), floatc(fat))))
            width(tb, ustr(T[eng][lang]))
            k.jnot(f'cabe_{lang}_{tb}', callmath('Greater_FloatFloat', inst('UiW'), inst('UiE')))
            sc = callmath('Divide_FloatFloat', inst('UiE'), inst('UiW'))
            k.st(context(inst(tb), final('SetRenderScale', callmath('MakeVector2D', sc, sc))))
            k.jmp(f'feito_{lang}_{tb}')
            k.label(f'cabe_{lang}_{tb}')  # cabe (ex.: depois de trocar de idioma): escala normal
            k.st(context(inst(tb), final('SetRenderScale', callmath('MakeVector2D', floatc(1.0), floatc(1.0)))))
            k.label(f'feito_{lang}_{tb}')
        k.jnot('fim_mede', callmath('Greater_FloatFloat', inst('UiE'), floatc(0.0)))
        k.st(letinst('UiFitLang', inst('UiLang')))
        k.jmp('fim_mede')
        k.label('nao_mede_' + lang)
    k.label('fim_mede')
def lang_fit(k): lang_block(k); fit_block(k)
def builder(fill):
    def b(base):
        k = Asm(base); fill(k); code, mem, _ = k.build(); return code, mem
    return b

if NAME == 'UI_CommunityMemberInfo':
    FN = p.export_index('UpdateInfo') - 1
    def local(n): return cat(op(0x00), path(n, FN + 1))
    def letlocal(n, v): return cat(op(0x0F), path(n, FN + 1), local(n), v)
    lines = stmts(FN); dt = Detour(p, FN); lv = local('ForceHidden')[0]
    # 1) idioma + rotulos: primeira instrucao do primeiro ramo da sequencia (nome do NPC), roda antes de status/agenda
    dt.detour(find(lines, lambda x: x == 'I:TextBlock_5->SetText(L:CallFunc_Conv_NameToText_ReturnValue)', 'nome'), builder(lang_fit), lv)
    # 2) agenda: depois das 5 strings e antes do uso (Concat com o switch do horario), troca pelas do texto oficial localizado
    #    (instrucao Array_Length logo depois: tamanho que o preenchimento do detour aceita)
    en = locres.read(os.path.join(HERE, '..', 'originais', 'locres', 'Game_en.locres'))
    pt = locres.read(os.path.join(HERE, '..', 'originais', 'locres', 'Game_pt-BR.locres'))
    def key_of(eng):
        ks = sorted(k for (ns, k), v in en.items() if ns == '' and v == eng and pt.get(('', k)))
        assert ks, eng; return ks[0]
    def sched(k):
        for var, eng in sorted(SCHEDULE.items()): k.st(letlocal(var, callmath('Conv_TextToString', textconst(eng, key_of(eng)))))
    dt.detour(find(lines, lambda x: x.startswith('let L:CallFunc_Array_Length_ReturnValue_2 = '), 'agenda'),
              builder(sched), lv)
    # 3) status: "Status" e "N/A" do Format e o "Status: N/A" fixo
    dt.detour(find(lines, lambda x: x.startswith("let L:CallFunc_MakeLiteralText_ReturnValue = ") and "text('Status')" in x, 'status'),
              builder(lambda k: k.st(letlocal('CallFunc_MakeLiteralText_ReturnValue', callmath('Conv_StringToText', inst('UiStatus'))))), lv)
    dt.detour(find(lines, lambda x: x == "let L:Temp_text_Variable_5 = text('N/A')", 'na'),
              builder(lambda k: k.st(letlocal('Temp_text_Variable_5', callmath('Conv_StringToText', inst('UiNA'))))), lv)
    dt.detour(find(lines, lambda x: x == "I:TextBlock->SetText(text('Status: N/A'))", 'status na'),
              builder(lambda k: k.st(settext('TextBlock', callmath('Concat_StrStr', callmath('Concat_StrStr', inst('UiStatus'), ustr(': ')),
                                                                     inst('UiNA'))))), lv)
    dt.commit()
    FIRST, LAST = ('BP_InvPRevWidget_NPC', 'ObjectProperty'), ('TraitsKey', 'StrProperty', 47)
elif NAME == 'UI_CommunityMember':  # linha do membro na lista (UpdateInfo a cada atualizacao da aba)
    FN = p.export_index('UpdateInfo') - 1
    lines = stmts(FN); dt = Detour(p, FN); lv = cat(op(0x00), path('MoralPercent', FN + 1))[0]
    dt.detour(find(lines, lambda x: x == 'I:TextBlock_5->SetText(L:CallFunc_Conv_NameToText_ReturnValue)', 'nome'), builder(lang_fit), lv)
    dt.commit()
    FIRST, LAST = ('UberGraphFrame', 'StructProperty'), ('OnSelected', 'MulticastInlineDelegateProperty', 51)
else:
    FN = p.export_index('ExecuteUbergraph_' + NAME) - 1
    lines = stmts(FN)
    lv = cat(op(0x00), path('CallFunc_GetWorldSubsystem_ReturnValue', FN + 1))[0]
    def at(m, start):
        r = [(q, x) for q, mm, x in lines if mm == m]; assert r and r[0][1].startswith(start), (m, r[:1]); return r[0][0]
    dt = Detour(p, FN)
    if NAME == 'UI_CommunityTab':
        # OnInitialized -> ExecuteUbergraph(6912): textos (o Slate ainda nao existe, nao da para medir)
        dt.detour(at(6912, 'let L:CallFunc_GetActorOfClass_ReturnValue = '), builder(lang_block), lv)
        # Event_UIData (6680, timer de 2 s) e OnTabFocus (7005 -> 7050): troca de idioma em jogo + medir/ajustar com a aba visivel
        dt.detour(at(6680, 'let L:CallFunc_GetWorldSubsystem_ReturnValue_1 = '), builder(lang_fit), lv)
        dt.detour(at(7050, 'let L:CallFunc_GetOwningPlayer_ReturnValue_2 = '), builder(lang_fit), lv)
        FIRST, LAST = ('UberGraphFrame', 'StructProperty'), ('CommIndex', 'IntProperty', 47)
    else:  # UI_PreTaskInfo: Update -> ExecuteUbergraph(10)
        dt.detour(at(10, 'let L:CallFunc_GetDataTableRowFromName_ReturnValue = '), builder(lang_fit), lv)
        FIRST, LAST = ('UberGraphFrame', 'StructProperty'), ('TextBlock_7', 'ObjectProperty', 51)
    dt.commit()

# ---- quebra de linha: AutoWrapText=true e Justification=Center nas propriedades (tagged) do TextBlock no WidgetTree
def tag_end(blob):
    """posicao do FName None que fecha a lista de propriedades de um export"""
    q = 0
    while True:
        n = a.fn(*struct.unpack_from('<ii', blob, q)); q += 8
        if n == 'None': return q - 8
        t = a.fn(*struct.unpack_from('<ii', blob, q)); q += 8; size = struct.unpack_from('<i', blob, q)[0]; q += 8
        q += {'StructProperty': 24, 'BoolProperty': 1, 'ByteProperty': 8, 'EnumProperty': 8, 'ArrayProperty': 8,
              'SetProperty': 8, 'MapProperty': 16}.get(t, 0)
        q += 1 + (16 if blob[q] else 0) + size
for tb in WRAP.get(NAME, []):
    i = [k for k, e in enumerate(a.exports) if e['name'] == tb and a.obj(e['cls']).endswith('TextBlock')]; assert len(i) == 1, tb
    blob = bytearray(p.blobs[i[0]]); q = tag_end(blob)
    tags = (fname('AutoWrapText') + fname('BoolProperty') + I32(0) + I32(0) + b'\1' + b'\0'
            + fname('Justification') + fname('ByteProperty') + I32(8) + I32(0) + fname('ETextJustify') + b'\0'
            + fname('ETextJustify::Center'))
    blob[q:q] = tags; p.blobs[i[0]] = bytes(blob)

# ---- props novas (StrProperty, transientes) no fim das propriedades da classe
blob = bytearray(p.blobs[CLS])
def key_prop(name, typ): return fname(typ) + fname(name)
q_first = blob.find(key_prop(*FIRST)); assert q_first > 0
cnt = struct.unpack_from('<i', blob, q_first - 4)[0]
q_last = blob.find(key_prop(*LAST[:2])); assert q_last > q_first
OBJF = struct.unpack_from('<I', blob, q_last + 16)[0]
new = b''.join(fname(t) + fname(n) + U32(OBJF) + I32(1) + I32(sz) + struct.pack('<Q', 0x2000) + b'\0\0' + I32(p.name('None'))
               + I32(0) + b'\0' for n, t, sz in [(n, 'StrProperty', 16) for n in PROPS] + [(n, 'FloatProperty', 4) for n in FPROPS])
end = q_last + LAST[2]
blob[end:end] = new
struct.pack_into('<i', blob, q_first - 4, cnt + len(PROPS) + len(FPROPS))
p.blobs[CLS] = bytes(blob)

os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, NAME + '.uasset'), os.path.join(outdir, NAME + '.uexp'))
open(os.path.join(outdir, NAME + '.full'), 'wb').write(full)
print(f'{NAME}: textos traduzidos ({len(LABELS[NAME])} rotulos, {len(LANGS)} idiomas); props {cnt}->{cnt + len(PROPS) + len(FPROPS)}', len(full))
