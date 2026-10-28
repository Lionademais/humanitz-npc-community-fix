# BP_HMZQuestComp: subsistema de comunidade no cliente sem alterar o executavel.
#  O UHZCommunityNPCSubSys nativo so e criado no host/single-player (ShouldCreateSubsystem recusa NM_Client).
#  Acrescenta:
#   - propriedade CommSubInst (objeto HZCommunityNPCSubSys, transiente, nao replicada), sempre no fim da lista
#   - funcao CommSubFix(Ctx, Cls) -> ReturnValue, com a mesma assinatura de GetWorldSubsystem:
#       R = GetWorldSubsystem(Ctx, Cls); se valido -> R            (servidor patchado, host, single-player)
#       se IsServer(Ctx) -> None                                    (servidor sem subsistema: nao improvisa)
#       QC = GetPlayerController(Ctx, 0).GetComponentByClass(BP_HMZQuestComp_C)
#       se QC.CommSubInst invalido: cria com SpawnObject(HZCommunityNPCSubSys, Outer = mundo do PlayerController)
#                                   e faz o SetACtionDT(DT_TaskConfig) que o BP_GameStateBase faz no BeginPlay
#       -> QC.CommSubInst
#  A funcao nao usa 'self': as chamadas trocadas (swap_subsys.py) a executam com o objeto chamador como contexto.
#  O objeto criado nao recebe Initialize, entao nao roda Tick (IsTickable exige bInitialized): o cliente so guarda
#  os dados que o servidor sincroniza, sem simular nada localmente.
# Uso: build_commsub.py entrada.full saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg
from kasm import Asm

I32 = lambda v: struct.pack('<i', v)
U32 = lambda v: struct.pack('<I', v)
EXTRA = {'StructProperty': 4, 'ObjectProperty': 4, 'ClassProperty': 8, 'ByteProperty': 4, 'BoolProperty': 6, 'SoftObjectProperty': 4,
         'InterfaceProperty': 4, 'WeakObjectProperty': 4, 'SoftClassProperty': 8, 'DelegateProperty': 4, 'MulticastInlineDelegateProperty': 4,
         'MulticastSparseDelegateProperty': 4, 'LazyObjectProperty': 4}

def skip_field(p, b, q):
    t = p.a.fn(*struct.unpack_from('<ii', b, q)); q += 47
    if t in ('ArrayProperty', 'SetProperty'): return skip_field(p, b, q)
    if t == 'MapProperty': return skip_field(p, b, skip_field(p, b, q))
    if t == 'EnumProperty': return skip_field(p, b, q) + 4
    assert t.endswith('Property'), t
    return q + EXTRA.get(t, 0)

def build(src, outdir):
    p = Pkg(src); a = p.a
    def exp_idx(name): return [i for i, e in enumerate(a.exports) if e['name'] == name][0]
    CLS = exp_idx('BP_HMZQuestComp_C'); TPL = exp_idx('IsCommunityFull')
    def imp(cls, name):
        r = p.find_import(cls, name); assert r, (cls, name); return r
    def fname(n, num=0): return I32(p.name(n)) + I32(num)
    COREPKG, ENGPKG = imp('Package', '/Script/CoreUObject'), imp('Package', '/Script/Engine')
    SUBSYS = imp('Class', 'HZCommunityNPCSubSys')
    C_OBJECT = p.add_import('/Script/CoreUObject', 'Class', COREPKG, 'Object')
    C_CLASS = p.add_import('/Script/CoreUObject', 'Class', COREPKG, 'Class')
    C_KSL = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'KismetSystemLibrary')
    C_GPS = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'GameplayStatics')
    C_ACTOR = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'Actor')
    C_KML = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'KismetMathLibrary')
    C_QC = CLS + 1
    F = {n: imp('Function', n) for n in ('GetWorldSubsystem',)}
    for c, names in ((C_KSL, ('IsValid', 'IsServer', 'GetOuterObject')), (C_GPS, ('GetPlayerController', 'SpawnObject')),
                     (C_ACTOR, ('GetComponentByClass',)), (C_KML, ('Not_PreBool',)), (SUBSYS, ('SetACtionDT',))):
        for n in names: F[n] = p.add_import('/Script/CoreUObject', 'Function', c, n)
    DTP = p.add_import('/Script/CoreUObject', 'Package', 0, '/Game/TSS_Game/KaiAIMapTest/KaiHumanAI/Quest/QuestPreset/Random/Recruit/Data/DT_TaskConfig')
    DT = p.add_import('/Script/Engine', 'DataTable', DTP, 'DT_TaskConfig')

    me = p.ec + 1  # indice 1-based do novo export
    NULLPATH = (I32(0) + I32(0), 8)
    def cat(*parts): return b''.join(x[0] for x in parts), sum(x[1] for x in parts)
    def op(c): return bytes([c]), 1
    def objref(i): return I32(i), 8
    def ppath(n, owner): return I32(1) + fname(n) + I32(owner), 8
    def L(n): return cat(op(0x00), ppath(n, me))
    def OUT(n): return cat(op(0x48), ppath(n, me))
    def inst(n): return cat(op(0x01), ppath(n, C_QC))
    def final(fn, *args): return cat(op(0x1C), objref(fn), *args, op(0x16))
    def callmath(fn, *args): return cat(op(0x68), objref(fn), *args, op(0x16))
    def context(obj, expr, rv=NULLPATH): return cat(op(0x19), obj, (U32(expr[1]), 4), rv, expr)
    def objconst(i): return cat(op(0x20), objref(i))
    def letobj(lhs, rhs): return cat(op(0x5F), lhs, rhs)
    def intc(v): return cat(op(0x1D), (I32(v), 4))
    def valid(x): return callmath(F['IsValid'], x)

    k = Asm(0)
    k.st(letobj(L('Real'), callmath(F['GetWorldSubsystem'], L('Ctx'), L('Cls'))))
    k.jnot('fallback', valid(L('Real')))
    k.st(letobj(OUT('ReturnValue'), L('Real'))); k.jmp('end')
    k.label('fallback')
    k.jnot('end', callmath(F['Not_PreBool'], callmath(F['IsServer'], L('Ctx'))))
    k.st(letobj(L('PC'), callmath(F['GetPlayerController'], L('Ctx'), intc(0))))
    k.jnot('end', valid(L('PC')))
    k.st(letobj(L('QC'), context(L('PC'), final(F['GetComponentByClass'], objconst(C_QC)))))
    k.jnot('end', valid(L('QC')))
    k.st(letobj(L('Inst'), context(L('QC'), inst('CommSubInst'))))
    k.jnot('create', valid(L('Inst')))  # sem instancia -> cria
    k.jmp('ret')
    k.label('create')
    world = callmath(F['GetOuterObject'], callmath(F['GetOuterObject'], L('PC')))
    k.st(letobj(L('Inst'), callmath(F['SpawnObject'], objconst(SUBSYS), world)))
    k.st(letobj(context(L('QC'), inst('CommSubInst')), L('Inst')))
    k.st(context(L('Inst'), final(F['SetACtionDT'], objconst(DT))))
    k.label('ret')
    k.st(letobj(OUT('ReturnValue'), L('Inst')))
    k.label('end')
    k.st(cat(op(0x04), OUT('ReturnValue'))); k.st(op(0x53))  # como o compilador: return OUT:ReturnValue
    code, cmem, labels = k.build()

    # propriedades da funcao: parametros primeiro (ReturnValue, Ctx, Cls), depois os locais
    def fprop(fclass, name, pflags, esize, extra=b''):
        return fname(fclass) + fname(name) + U32(1) + I32(1) + I32(esize) + struct.pack('<Q', pflags) + b'\0\0' + fname('None') + b'\0' + extra
    def objp(name, cls, pflags): return fprop('ObjectProperty', name, pflags, 8, I32(cls))
    props = [objp('ReturnValue', SUBSYS, 0x580), objp('Ctx', C_OBJECT, 0x80), objp('Cls', C_CLASS, 0x80),
             objp('Real', SUBSYS, 0), objp('PC', C_OBJECT, 0), objp('QC', C_OBJECT, 0), objp('Inst', SUBSYS, 0)]
    blob = fname('None') + I32(0) + I32(0) + I32(0) + I32(len(props)) + b''.join(props)
    blob += I32(cmem) + I32(len(code)) + code
    blob += U32(0x0CC22000) + I32(0) + I32(0)  # BlueprintCallable|BlueprintEvent|HasDefaults|HasOutParms|Public|Static
    idx = p.add_export(TPL, 'CommSubFix', CLS + 1, blob, ([], [me], [], [CLS + 1]))
    assert idx == me
    sbs, cbs, sbc, cbc = p.deps[idx - 1]
    p.set_deps(idx - 1, (sbs, cbs + [DT], sbc, cbc))
    print(f'CommSubFix: export {me}, script {len(code)} disco / {cmem} mem, rotulos {labels}')

    # classe: Children, FuncMap, nova propriedade CommSubInst no fim
    cb = bytearray(p.blobs[CLS])
    q = 74; n = struct.unpack_from('<i', cb, q)[0]
    kids = [struct.unpack_from('<i', cb, q + 4 + 4 * i)[0] for i in range(n)]
    cb[q + 4 + 4 * n:q + 4 + 4 * n] = I32(me); struct.pack_into('<i', cb, q, n + 1)
    fm = None
    for z in range(q + 4 + 4 * (n + 1), len(cb) - 4):
        if struct.unpack_from('<i', cb, z)[0] == n and z + 4 + 12 * n <= len(cb) and all(
                struct.unpack_from('<i', cb, z + 12 + 12 * j)[0] in kids for j in range(n)):
            fm = z; break
    assert fm, 'FuncMap nao encontrado'
    cb[fm + 4 + 12 * n:fm + 4 + 12 * n] = fname('CommSubFix') + I32(me); struct.pack_into('<i', cb, fm, n + 1)
    key = fname('StructProperty') + fname('UberGraphFrame'); qu = cb.find(key); assert qu > 0
    cnt = struct.unpack_from('<i', cb, qu - 4)[0]; qe = qu
    for _ in range(cnt): qe = skip_field(p, cb, qe)
    newp = fname('ObjectProperty') + fname('CommSubInst') + U32(struct.unpack_from('<I', cb, qu + 16)[0]) + I32(1) + I32(8) + \
        struct.pack('<Q', 0x2000) + b'\0\0' + fname('None') + b'\0' + I32(SUBSYS)  # CPF_Transient
    # SyncUI: dialogo UI_HMZQuest aberto, para o CLIENT_NPCSync redesenhar as traits (ver build_rpcs/build_uiquest)
    newp += fname('ObjectProperty') + fname('SyncUI') + U32(struct.unpack_from('<I', cb, qu + 16)[0]) + I32(1) + I32(8) + \
        struct.pack('<Q', 0x2000) + b'\0\0' + fname('None') + b'\0' + I32(C_OBJECT)
    cb[qe:qe] = newp; struct.pack_into('<i', cb, qu - 4, cnt + 2)
    p.blobs[CLS] = bytes(cb)
    sbs, cbs, sbc, cbc = p.deps[CLS]; p.set_deps(CLS, (sbs, cbs + [me], sbc, cbc))
    print(f'props {cnt}->{cnt + 2}')
    os.makedirs(outdir, exist_ok=True)
    full = p.save(os.path.join(outdir, 'BP_HMZQuestComp.uasset'), os.path.join(outdir, 'BP_HMZQuestComp.uexp'))
    open(os.path.join(outdir, 'BP_HMZQuestComp.full'), 'wb').write(full)
    print('ok', len(full))

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
