# BP_GameModeSave."Save Progress": so grava HZ_SaveSlot.NPCCommunityData se o subsistema de comunidade existir.
# Sem a correcao nativa (servidor dedicado), GetWorldSubsystem devolve nulo, GetWorldCommunityData devolve mapa vazio e
# o save apagava todas as comunidades. Com o desvio, o HZ_SaveSlot carregado mantem os dados ate a correcao voltar.
# Uso: patch_savecomm.py BP_GameModeSave_srv.bin saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import Dis, find_script
from detour import Detour
src, outdir = sys.argv[1:3]
os.makedirs(outdir, exist_ok=True)
p = Pkg(src); a = p.a; d = a.d
SP = [i for i, e in enumerate(a.exports) if e['name'] == 'Save Progress'][0]
s0, e0 = find_script(a, a.exports[SP])
lines = Dis(a, s0, e0).run()
def find(txt, after=0):
    return [(pos, m) for pos, m, x in lines if txt in x and pos > after][0]
GS, _ = find('let L:CallFunc_GetWorldSubsystem_ReturnValue = /Script/Engine.SubsystemBlueprintLibrary.GetWorldSubsystem(self, obj(/Script/TSSGame.HZCommunityNPCSubSys))')
find('HZCommunityNPCSubSys.GetWorldCommunityData()', GS)
AS, _ = find('let I:HZ_SaveSlot->I:NPCCommunityData = L:CallFunc_GetWorldCommunityData_ReturnValue', GS)
i = [k for k, (pos, m, x) in enumerate(lines) if pos == AS][0]
SKIP = lines[i + 1][1]  # memoria da instrucao seguinte a atribuicao
assert d[GS] == 0x5F and d[GS + 1] == 0x00
SUB = bytes(d[GS + 1:GS + 18])  # EX_LocalVariable L:CallFunc_GetWorldSubsystem_ReturnValue
IV, _ = find('KismetSystemLibrary.IsValid(L:')
assert d[IV] == 0x14 and d[IV + 18] == 0x68
ISVALID = bytes(d[IV + 18:IV + 23])  # EX_CallMath KismetSystemLibrary.IsValid
cond = ISVALID + SUB + b'\x16'
extra = b'\x07' + struct.pack('<I', SKIP) + cond, 5 + (1 + 8 + 9 + 1)
dt = Detour(p, SP)
dt.detour(GS, lambda m: extra, SUB)
dt.commit()
full = p.save(os.path.join(outdir, 'BP_GameModeSave.uasset'), os.path.join(outdir, 'BP_GameModeSave.uexp'))
open(os.path.join(outdir, 'BP_GameModeSave.full'), 'wb').write(full); print('BP_GameModeSave ok', len(full))
