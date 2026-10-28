# Desmontar a Base da Comunidade no servidor dedicado:
#  C-Building.DestroyBuilding: antes de IActor->OnDismantled(), grava IActor.Player = L:Player (quem desmontou)
#  BPK_CommunityBaseLevel1 (OnDismantled): GetPlayerController(self, 0) -> I:Player->I:OwningPlayerController (3x)
# Uso: patch_dismantle.py cbuilding.full base.bin saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from reloc import edit_function
from detour import Detour
cb_src, base_src, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
# ---- C-Building
p = Pkg(cb_src); a = p.a; d = a.d
DB = [i for i, e in enumerate(a.exports) if e['name'] == 'DestroyBuilding'][0]
POS, PL = 287474, 287332  # L:IActor->OnDismantled() ; L:Player->TakeHammerDur(true)
assert d[POS] == 0x19 and d[POS + 1] == 0x00 and d[PL] == 0x19 and d[PL + 1] == 0x00
IACTOR, PLAYER = bytes(d[POS + 1:POS + 18]), bytes(d[PL + 1:PL + 18])
C_BIA = p.find_import('BlueprintGeneratedClass', 'BP_BaseInteractActor_C'); assert C_BIA
PP = struct.pack('<iii', 1, p.name('Player'), 0) + struct.pack('<i', C_BIA)
lhs = b'\x19' + IACTOR + struct.pack('<I', 9) + PP + b'\x01' + PP
st = b'\x5f' + lhs + PLAYER; st_mem = 1 + (1 + 9 + 4 + 8 + 9) + 9
orig_end = POS + 1 + 17 + 4 + 8 + 1 + 8 + 1  # 19 L:IActor skip rv(nulo) 45 FName 16
assert d[orig_end - 1] == 0x16 and d[orig_end] == 0x4D
edit_function(p, DB, [(POS, st + bytes(d[POS:orig_end]), st_mem + (1 + 9 + 4 + 8 + 1 + 12 + 1))])
full = p.save(os.path.join(outdir, 'C-Building.uasset'), os.path.join(outdir, 'C-Building.uexp'))
open(os.path.join(outdir, 'C-Building.full'), 'wb').write(full); print('C-Building ok', len(full))
# ---- BPK_CommunityBaseLevel1 (servidor)
p = Pkg(base_src); a = p.a; d = a.d
UG = [i for i, e in enumerate(a.exports) if e['name'] == 'ExecuteUbergraph_BPK_CommunityBaseLevel1'][0]
CTX = 56629  # Context(I:Player)->I:OwningPlayerController (em WidgetCreated)
ctx = bytes(d[CTX:CTX + 55]); assert ctx[0] == 0x19 and ctx[38] == 0x01
dt = Detour(p, UG)
for pos in (43512, 43791, 44010):
    assert d[pos] == 0x5F and d[pos + 18] == 0x68
    lv = bytes(d[pos + 1:pos + 18])
    new = (b'\x5f' + lv + ctx, 1 + 9 + 31)
    dt.detour(pos, lambda m, new=new: new, lv)
dt.commit()
full = p.save(os.path.join(outdir, 'BPK_CommunityBaseLevel1.uasset'), os.path.join(outdir, 'BPK_CommunityBaseLevel1.uexp'))
open(os.path.join(outdir, 'BPK_CommunityBaseLevel1.full'), 'wb').write(full); print('Base ok', len(full))
