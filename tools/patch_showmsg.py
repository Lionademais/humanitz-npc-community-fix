# BP_HMZQuestComp (cliente): aviso de comunidade restaurada numa janela grande, na lingua do jogo.
# O servidor (build_sync --server) envia CLIENT_ShowQuestMessage com o titulo MSG_KEY e o texto em ingles (cliente antigo
# mostra no popup pequeno de missao). Aqui, no inicio do CLIENT_ShowQuestMessage, se Title == MSG_KEY:
#   - troca Title/Data pelo texto da cultura atual (GetCurrentCulture, a mesma que o BP_GameInstanceWithSettings usa);
#   - abre UI_HZ_Tutorial_PopUp (janela central do tutorial; textos achados por Tut_Img.GetParent().GetChildAt(0/2),
#     imagem Tut_Img escondida, botao Continue); o Construct dela grava BP_CharacterBase.TutWidget, e o jogo fecha com Continue/pulo;
#   - guarda a janela em SyncMsgW (prop de build_sync) e ignora o segundo envio do servidor; nao mostra o popup pequeno.
# Uso: patch_showmsg.py BP_HMZQuestComp.full saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import find_script
from kasm import Asm

MSG_KEY = 'Community restored'
TEXTS = [  # prefixo da cultura, titulo, texto (ingles fica como padrao, igual ao enviado pelo servidor)
    ('pt', 'Comunidade restaurada',
     'Sua base estava sem comunidade: ela foi construída ou melhorada enquanto a correção de comunidade do servidor estava '
     'desativada (normalmente logo depois de uma atualização do jogo ou do mod). A comunidade foi recriada, mas os '
     'sobreviventes que estavam nela não puderam ser recuperados. Renomeie a comunidade na base. Isso não vai acontecer '
     'novamente nas futuras atualizações.'),
    ('de', 'Gemeinschaft wiederhergestellt',
     'Deine Basis hatte keine Gemeinschaft: Sie wurde gebaut oder ausgebaut, während der Gemeinschafts-Fix des Servers '
     'inaktiv war (meist direkt nach einem Spiel- oder Mod-Update). Die Gemeinschaft wurde neu erstellt, aber die '
     'Überlebenden, die darin waren, konnten nicht wiederhergestellt werden. Benenne die Gemeinschaft an der Basis um. '
     'Das wird bei zukünftigen Updates nicht mehr passieren.'),
    ('es', 'Comunidad restaurada',
     'Tu base no tenía comunidad: se construyó o mejoró mientras la corrección de comunidad del servidor estaba '
     'desactivada (normalmente justo después de una actualización del juego o del mod). La comunidad se ha recreado, '
     'pero los supervivientes que estaban en ella no se pudieron recuperar. Cambia el nombre de la comunidad en la base. '
     'Esto no volverá a ocurrir en futuras actualizaciones.'),
    ('fr', 'Communauté restaurée',
     "Votre base n'avait pas de communauté : elle a été construite ou améliorée pendant que le correctif de communauté du "
     "serveur était inactif (généralement juste après une mise à jour du jeu ou du mod). La communauté a été recréée, mais "
     "les survivants qui en faisaient partie n'ont pas pu être récupérés. Renommez la communauté depuis la base. Cela ne "
     "se reproduira plus lors des prochaines mises à jour."),
    ('it', 'Comunità ripristinata',
     'La tua base non aveva una comunità: è stata costruita o migliorata mentre la correzione della comunità del server '
     'era disattivata (di solito subito dopo un aggiornamento del gioco o della mod). La comunità è stata ricreata, ma i '
     'sopravvissuti che ne facevano parte non sono stati recuperati. Rinomina la comunità dalla base. Non succederà più '
     'nei prossimi aggiornamenti.'),
    ('ja', 'コミュニティが復元されました',
     'あなたの拠点にはコミュニティがありませんでした。サーバーのコミュニティ修正が無効な間（通常はゲームやMODの'
     'アップデート直後）に建設またはアップグレードされたためです。コミュニティは再作成されましたが、所属していた'
     '生存者は復元できませんでした。拠点でコミュニティの名前を変更してください。今後のアップデートでこれが再び'
     '起こることはありません。'),
    ('ko', '공동체 복구됨',
     '기지에 공동체가 없었습니다. 서버의 공동체 수정이 비활성화된 동안(보통 게임이나 모드 업데이트 직후) 건설되거나 '
     '업그레이드되었기 때문입니다. 공동체는 다시 만들어졌지만, 소속되어 있던 생존자는 복구할 수 없었습니다. 기지에서 '
     '공동체 이름을 변경하세요. 앞으로의 업데이트에서는 다시 발생하지 않습니다.'),
    ('ru', 'Община восстановлена',
     'У вашей базы не было общины: она была построена или улучшена, пока исправление общин на сервере было неактивно '
     '(обычно сразу после обновления игры или мода). Община создана заново, но выживших, которые в ней были, '
     'восстановить не удалось. Переименуйте общину на базе. В будущих обновлениях это больше не повторится.'),
    ('zh', '社区已恢复',
     '你的基地没有社区：它是在服务器的社区修复未启用时（通常是在游戏或模组更新之后）建造或升级的。社区已重新创建，'
     '但其中的幸存者无法恢复。请在基地处重命名社区。今后的更新中不会再发生这种情况。'),
]

src, outdir = sys.argv[1:3]
p = Pkg(src); a = p.a
I32 = lambda v: struct.pack('<i', v)
FN = p.export_index('CLIENT_ShowQuestMessage') - 1  # 0-based
CLS = p.export_index('BP_HMZQuestComp_C') - 1
ENG, UMG = p.find_import('Package', '/Script/Engine'), p.find_import('Package', '/Script/UMG'); assert ENG and UMG
def cls(pkg, name): return p.find_import('Class', name, pkg) or p.add_import('/Script/CoreUObject', 'Class', pkg, name)
def fn(c, name): return p.add_import('/Script/CoreUObject', 'Function', c, name)
C_STR, C_I18N, C_TXT, C_SYS = (cls(ENG, n) for n in ('KismetStringLibrary', 'KismetInternationalizationLibrary', 'KismetTextLibrary', 'KismetSystemLibrary'))
C_PC, C_WBL, C_UW, C_W, C_TB = cls(ENG, 'PlayerController'), cls(UMG, 'WidgetBlueprintLibrary'), cls(UMG, 'UserWidget'), cls(UMG, 'Widget'), cls(UMG, 'TextBlock')
F_EQ, F_SW, F_CUL, F_S2T = fn(C_STR, 'EqualEqual_StrStr'), fn(C_STR, 'StartsWith'), fn(C_I18N, 'GetCurrentCulture'), fn(C_TXT, 'Conv_StringToText')
F_VALID, F_OWNER = fn(C_SYS, 'IsValid'), p.find_import('Function', 'GetOwner'); assert F_OWNER
C_PANEL = cls(UMG, 'PanelWidget')
# GetWidgetFromName NAO e UFUNCTION nesta build (import nulo -> crash em CallFunction); usar GetParent/GetChildAt
F_CREATE, F_ADDVP = fn(C_WBL, 'Create'), fn(C_UW, 'AddToViewport')
F_PARENT, F_CHILD = fn(C_W, 'GetParent'), fn(C_PANEL, 'GetChildAt')
F_SETVIS, F_SETTEXT = fn(C_W, 'SetVisibility'), fn(C_TB, 'SetText')
PK_TUT = p.add_import('/Script/CoreUObject', 'Package', 0, '/Game/TSS_Game/UI/Tutorial/UI_HZ_Tutorial_PopUp')
C_TUT = p.add_import('/Script/UMG', 'WidgetBlueprintGeneratedClass', PK_TUT, 'UI_HZ_Tutorial_PopUp_C')

def cat(*parts): return b''.join(x[0] for x in parts), sum(x[1] for x in parts)
def op(c): return bytes([c]), 1
def path(n, owner): return I32(1) + I32(p.name(n)) + I32(0) + I32(owner + 1), 8
NULLPATH = (I32(0) + I32(0), 8)
def local(n): return cat(op(0x00), path(n, FN))
def inst(n): return cat(op(0x01), path(n, CLS))
def objref(i): return I32(i), 8
def callmath(f, *args): return cat(op(0x68), objref(f), *args, op(0x16))
def final(f, *args): return cat(op(0x1C), objref(f), *args, op(0x16))
def context(obj, call): return cat(op(0x19), obj, (struct.pack('<I', call[1]), 4), NULLPATH, call)
def dcast(c, x): return cat(op(0x2E), objref(c), x)
def namec(n, num=0): return cat(op(0x21), (I32(p.name(n)) + I32(num), 12))
def ustr(t):
    try: return cat(op(0x1F), (t.encode('ascii') + b'\0', len(t) + 1))
    except UnicodeEncodeError: b = t.encode('utf-16-le') + b'\0\0'; return cat(op(0x34), (b, len(b)))
def let(n, rhs): return cat(op(0x0F), path(n, FN), local(n), rhs)
W = inst('SyncMsgW')
def ipath(n, owner_imp): return I32(1) + I32(p.name(n)) + I32(0) + I32(owner_imp), 8
def ctx_rv(obj, call, rv): return cat(op(0x19), obj, (struct.pack('<I', call[1]), 4), rv, call)
# arvore: Overlay_1 -> VerticalBox_1 [0 Tutorial (titulo), 1 Tut_Line, 2 TextBlock_443 (texto), 3 Tut_Img]
IMG = ctx_rv(dcast(C_TUT, W), cat(op(0x01), ipath('Tut_Img', C_TUT)), ipath('Tut_Img', C_TUT))
VBOX = context(IMG, final(F_PARENT))
def child(i): return dcast(C_TB, context(VBOX, final(F_CHILD, cat(op(0x1D), (I32(i), 4)))))

k = Asm(0)
k.jnot('orig', callmath(F_EQ, local('Title'), ustr(MSG_KEY)))
k.jnot('make', callmath(F_VALID, W)); k.st(cat(op(0x04), op(0x0B)))  # ja aberta (segundo envio): nada
k.label('make')
for pre, title, text in TEXTS:
    k.jnot('n_' + pre, callmath(F_SW, callmath(F_CUL), ustr(pre), cat(op(0x24), (b'\x01', 1))))  # IgnoreCase
    k.st(let('Title', ustr(title))); k.st(let('Data', ustr(text))); k.jmp('show')
    k.label('n_' + pre)
k.label('show')
k.st(cat(op(0x5F), W, callmath(F_CREATE, op(0x17), cat(op(0x20), objref(C_TUT)), dcast(C_PC, final(F_OWNER)))))
k.jnot('orig', callmath(F_VALID, W))  # sem janela: popup pequeno
k.st(context(child(0), final(F_SETTEXT, callmath(F_S2T, local('Title')))))
k.st(context(child(2), final(F_SETTEXT, callmath(F_S2T, local('Data')))))
k.st(context(IMG, final(F_SETVIS, cat(op(0x24), (b'\x01', 1)))))  # Collapsed
k.st(context(W, final(F_ADDVP, cat(op(0x1D), (I32(50), 4)))))
k.st(cat(op(0x04), op(0x0B)))
k.label('orig')
code, cmem, labels = k.build()

e = a.exports[FN]; s0, e0 = find_script(a, e); mem0, disk0 = struct.unpack_from('<ii', a.d, s0 - 8)
blob = bytearray(p.blobs[FN]); rs = s0 - e['off']
blob[rs:rs] = code
struct.pack_into('<ii', blob, rs - 8, mem0 + cmem, disk0 + len(code))
p.blobs[FN] = bytes(blob)
sbs, cbs, sbc, cbc = p.deps[FN]
p.set_deps(FN, (sbs, cbs + [C_TUT], sbc, cbc))
os.makedirs(outdir, exist_ok=True)
full = p.save(os.path.join(outdir, 'BP_HMZQuestComp.uasset'), os.path.join(outdir, 'BP_HMZQuestComp.uexp'))
open(os.path.join(outdir, 'BP_HMZQuestComp.full'), 'wb').write(full)
print(f'CLIENT_ShowQuestMessage: +{len(code)} bytes ({len(TEXTS)} linguas + ingles, janela UI_HZ_Tutorial_PopUp)', len(full))
