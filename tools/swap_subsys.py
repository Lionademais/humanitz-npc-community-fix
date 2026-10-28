# Troca, em todas as funcoes de um asset, "GetWorldSubsystem(<ctx>, HZCommunityNPCSubSys)" (EX_CallMath)
# por "CommSubFix(<ctx>, HZCommunityNPCSubSys)" (EX_FinalFunction de BP_HMZQuestComp_C, ver build_commsub.py).
# Mesmo tamanho em disco e em memoria: nenhum offset de salto muda.
# Uso: swap_subsys.py entrada(.bin|.full) saida_dir NomeDoAsset
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kismet import Dis, find_script
QC_PKG = '/Game/TSS_Game/KaiAIMapTest/KaiHumanAI/Quest/BP_HMZQuestComp'

def swap(src, outdir, asset):
    p = Pkg(src); a = p.a; d = a.d
    gws = [-(i + 1) for i, (c, o, n) in enumerate(a.imports) if c == 'Function' and n == 'GetWorldSubsystem']
    sub = p.find_import('Class', 'HZCommunityNPCSubSys'); assert gws and sub
    own = [i for i, e in enumerate(a.exports) if e['name'] == 'CommSubFix']
    if own: target = own[0] + 1
    else:
        cls = p.find_import('BlueprintGeneratedClass', 'BP_HMZQuestComp_C')
        if not cls:
            pk = p.find_import('Package', QC_PKG) or p.add_import('/Script/CoreUObject', 'Package', 0, QC_PKG)
            cls = p.add_import('/Script/Engine', 'BlueprintGeneratedClass', pk, 'BP_HMZQuestComp_C')
        target = p.add_import('/Script/CoreUObject', 'Function', cls, 'CommSubFix')
    total = 0
    for i, e in enumerate(a.exports):
        r = find_script(a, e) if e['size'] > 20 else None
        if not r: continue
        s0, e0 = r; blob = bytearray(p.blobs[i]); n = 0
        for g in gws:
            pat = b'\x68' + struct.pack('<i', g); q = d.find(pat, s0, e0)
            while q >= 0:
                x = Dis(a, q + 5, e0); x.expr()  # contexto (mundo)
                if d[x.p] == 0x20 and struct.unpack_from('<i', d, x.p + 1)[0] == sub and d[x.p + 5] == 0x16:
                    rel = q - e['off']; assert blob[rel] == 0x68
                    blob[rel] = 0x1C; struct.pack_into('<i', blob, rel + 1, target); n += 1
                q = d.find(pat, q + 1, e0)
        if n:
            p.blobs[i] = bytes(blob); total += n
            if target < 0:
                sbs, cbs, sbc, cbc = p.deps[i]
                if target not in cbs: p.set_deps(i, (sbs, cbs + [target], sbc, cbc))
            print(f'  {e["name"]}: {n}')
    os.makedirs(outdir, exist_ok=True)
    full = p.save(os.path.join(outdir, asset + '.uasset'), os.path.join(outdir, asset + '.uexp'))
    open(os.path.join(outdir, asset + '.full'), 'wb').write(full)
    print(f'{asset}: {total} chamadas trocadas, {len(full)} bytes')

if __name__ == '__main__':
    swap(sys.argv[1], sys.argv[2], sys.argv[3])
