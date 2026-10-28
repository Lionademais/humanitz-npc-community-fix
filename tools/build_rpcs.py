# BP_HMZQuestComp: acrescenta RPCs (cliente -> servidor) que repetem no servidor as acoes de gerenciar NPCs
# que a interface executa apenas no subsistema local. Uso: build_rpcs.py entrada.full saida_dir
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkg import Pkg

I32 = lambda v: struct.pack('<i', v)
U32 = lambda v: struct.pack('<I', v)

# nome -> (parametros, locais, corpo); tipos: guid byte name actor transform vector bool datatable
RPCS = {
    'SRV_AssignTask': ([('UID', 'guid'), ('CUID', 'guid'), ('PUID', 'guid'), ('Type', 'byte'), ('Tag', 'name'), ('Special', 'name'),
                        ('Target', 'actor'), ('TGuid', 'guid'), ('Trans', 'transform'), ('Sched', 'byte'), ('Danger', 'byte'), ('DT', 'datatable')],
                       [('Params', 'map')], 'AssignTaskToNPC'),
    'SRV_ScheduleTask': (None, None, 'ScheduleTaskForNPC'),  # mesmos parametros do Assign
    'SRV_ClearTask': ([('UID', 'guid'), ('CUID', 'guid'), ('PUID', 'guid'), ('Sched', 'byte')], [], 'ClearTaskFromNPC'),
    'SRV_Follow': ([('UID', 'guid'), ('Cmd', 'byte'), ('B1', 'bool'), ('B2', 'bool')], [('Found', 'bool')], 'SetNPCFollowCommand'),
    'SRV_Sleep': ([('UID', 'guid'), ('B', 'bool')], [('Found', 'bool')], 'ForceNPCToSleep'),
    'SRV_NPCHold': ([('NPC', 'actor'), ('B', 'bool'), ('V', 'vector')], [], 'SetHoldPos'),
    'SRV_NPCFriendly': ([('NPC', 'actor'), ('Pawn', 'actor'), ('Set', 'bool')], [], 'SetFriendly/ClearFriendly'),
    'SRV_FollowNPC': ([('NPC', 'actor'), ('Cmd', 'byte'), ('B1', 'bool'), ('B2', 'bool')], [('Found', 'bool')], 'SetNPCFollowCommand'),
    'SRV_NPCEquip': ([('NPC', 'actor'), ('Index', 'int'), ('Unequip', 'bool'), ('Destroyed', 'bool')], [], 'EquipItemByIndex/UnequipByIndex'),
    # sincronizacao dos TSet/TMap do NPCData (a replicacao nao transporta TSet/TMap): cliente pede, servidor responde
    'SRV_SyncNPC': ([('NPC', 'actor'), ('UID', 'guid')],
                    [('Data', 'npcdata'), ('Found', 'bool'), ('Tasks', 'bytearr'), ('Follow', 'bytearr'), ('PKeys', 'namearr'), ('PVals', 'floatarr')], None),
    'CLIENT_NPCSync': ([('NPC', 'actor'), ('Data', 'npcdata'), ('Tasks', 'bytearr'), ('Follow', 'bytearr'), ('PKeys', 'namearr'), ('PVals', 'floatarr')],
                       [('I', 'int'), ('K', 'name'), ('V', 'float')], None),
}
RPCS['SRV_ScheduleTask'] = (RPCS['SRV_AssignTask'][0], RPCS['SRV_AssignTask'][1], 'ScheduleTaskForNPC')

def build(src, outdir):
    p = Pkg(src); a = p.a
    def exp_idx0(name): return [i for i, e in enumerate(a.exports) if e['name'] == name][0]
    CLS = exp_idx0('BP_HMZQuestComp_C'); TPL = exp_idx0('SERVER_ChangeCamp')
    def imp(cls, name):
        r = p.find_import(cls, name); assert r, (cls, name); return r
    def fname(n, num=0): return I32(p.name(n)) + I32(num)
    COREPKG, ENGPKG = imp('Package', '/Script/CoreUObject'), imp('Package', '/Script/Engine')
    SUBSYS = imp('Class', 'HZCommunityNPCSubSys')
    S_GUID, S_TRANS, S_VEC = imp('ScriptStruct', 'Guid'), imp('ScriptStruct', 'Transform'), imp('ScriptStruct', 'Vector')
    C_ACTOR = imp('Class', 'Actor'); C_DT = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'DataTable')
    F_GETSUBSYS = imp('Function', 'GetWorldSubsystem')
    F_GETOWNER, F_NOT = imp('Function', 'GetOwner'), imp('Function', 'Not_PreBool')
    F_ISVALID = p.add_import('/Script/CoreUObject', 'Function', p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'KismetSystemLibrary'), 'IsValid')
    NAT = {n: p.add_import('/Script/CoreUObject', 'Function', SUBSYS, n)
           for n in ('AssignTaskToNPC', 'ScheduleTaskForNPC', 'ClearTaskFromNPC', 'SetNPCFollowCommand', 'ForceNPCToSleep', 'GetNPCDataByUID')}

    S_NPCDATA, C_NPC = imp('ScriptStruct', 'NPCRecruitData'), imp('Class', 'NativeHumanNPC')
    C_SETLIB = p.add_import('/Script/CoreUObject', 'Class', ENGPKG, 'BlueprintSetLibrary')
    O_SETLIB = p.add_import('/Script/Engine', 'BlueprintSetLibrary', ENGPKG, 'Default__BlueprintSetLibrary')
    C_MAPLIB = imp('Class', 'BlueprintMapLibrary'); O_MAPLIB = imp('BlueprintMapLibrary', 'Default__BlueprintMapLibrary')
    O_ARRLIB = imp('KismetArrayLibrary', 'Default__KismetArrayLibrary')
    LIBF = {n: p.add_import('/Script/CoreUObject', 'Function', C_SETLIB, n) for n in ('Set_ToArray', 'Set_Clear', 'Set_AddItems')}
    LIBF.update({n: p.add_import('/Script/CoreUObject', 'Function', C_MAPLIB, n) for n in ('Map_Keys', 'Map_Values', 'Map_Clear', 'Map_Add')})
    LIBF.update({n: imp('Function', n) for n in ('Array_Get', 'Array_Length', 'Less_IntInt', 'Add_IntInt')})
    def fprop(fclass, name, pflags, esize, extra=b''):
        return fname(fclass) + fname(name) + U32(1) + I32(1) + I32(esize) + struct.pack('<Q', pflags) + b'\0\0' + fname('None') + b'\0' + extra
    BOOLX = bytes.fromhex('01 00 01 ff 01 01')
    def typed(name, t, pflags):
        if t == 'guid': return fprop('StructProperty', name, pflags, 16, I32(S_GUID))
        if t == 'transform': return fprop('StructProperty', name, pflags, 48, I32(S_TRANS))
        if t == 'vector': return fprop('StructProperty', name, pflags, 12, I32(S_VEC))
        if t == 'byte': return fprop('ByteProperty', name, pflags, 1, I32(0))
        if t == 'name': return fprop('NameProperty', name, pflags, 12)
        if t == 'actor': return fprop('ObjectProperty', name, pflags, 8, I32(C_ACTOR))
        if t == 'datatable': return fprop('ObjectProperty', name, pflags, 8, I32(C_DT))
        if t == 'bool': return fprop('BoolProperty', name, pflags, 1, BOOLX)
        if t == 'npcdata': return fprop('StructProperty', name, pflags, 0, I32(S_NPCDATA))
        if t == 'int': return fprop('IntProperty', name, pflags, 4)
        if t == 'float': return fprop('FloatProperty', name, pflags, 4)
        af = 0x8000194 if pflags else 0
        if t == 'bytearr': return fprop('ArrayProperty', name, af, 16) + fprop('ByteProperty', name, 0, 1, I32(0))
        if t == 'namearr': return fprop('ArrayProperty', name, af, 16) + fprop('NameProperty', name, 0, 12)
        if t == 'floatarr': return fprop('ArrayProperty', name, af, 16) + fprop('FloatProperty', name, 0, 4)
        if t == 'map': return fprop('MapProperty', name, pflags, 80) + fprop('NameProperty', name, 0, 12) + fprop('StrProperty', name + '_Value', 0, 16)
        raise ValueError(t)

    # bytecode
    def cat(*parts): return b''.join(x[0] for x in parts), sum(x[1] for x in parts)
    def op(c): return bytes([c]), 1
    NULLPATH = (I32(0) + I32(0), 8)
    def objref(i): return I32(i), 8
    def final(fn, *args): return cat(op(0x1C), objref(fn), *args, op(0x16))
    def virtual(name, *args): return cat(op(0x1B), (fname(name), 12), *args, op(0x16))
    def callmath(fn, *args): return cat(op(0x68), objref(fn), *args, op(0x16))
    def context(obj, call, rv=NULLPATH): return cat(op(0x19), obj, (U32(call[1]), 4), rv, call)
    def objconst(i): return cat(op(0x20), objref(i))
    SELF = op(0x17)

    new_idx = []
    base_ec = p.ec
    for k, (fn, (params, locs, target)) in enumerate(RPCS.items()):
        me = base_ec + k + 1  # indice 1-based do novo export
        def L(n): return cat(op(0x00), (I32(1) + fname(n) + I32(me), 8))
        subsys = callmath(F_GETSUBSYS, SELF, objconst(SUBSYS))
        # host/single-player: a interface ja executou a acao no subsistema verdadeiro -> RPC de acao nao repete
        guarded = fn.startswith('SRV_') and fn != 'SRV_SyncNPC'
        islocal = callmath(F_NOT, context(final(F_GETOWNER), virtual('IsLocalController')))
        G = (1 + 4 + islocal[1]) if guarded else 0
        args = [L(n) for n, _ in params]
        if fn in ('SRV_AssignTask', 'SRV_ScheduleTask'):
            a2 = args[:9] + [L('Params')] + args[9:]
            body = [context(subsys, final(NAT[target], *a2))]
        elif fn == 'SRV_ClearTask':
            body = [context(subsys, final(NAT[target], *args))]
        elif fn in ('SRV_Follow', 'SRV_Sleep'):
            data = context(subsys, final(NAT['GetNPCDataByUID'], L('UID'), L('Found')))
            body = [context(subsys, final(NAT[target], data, *args[1:]))]
        elif fn == 'SRV_NPCHold':
            body = [context(L('NPC'), virtual('SetHoldPos', L('B'), L('V')))]
        elif fn == 'SRV_NPCFriendly':
            s_set = context(L('NPC'), virtual('SetFriendly', L('Pawn')))
            s_clr = context(L('NPC'), virtual('ClearFriendly', L('Pawn')))
            jn_len = 1 + 4 + L('Set')[1]; j_len = 5
            clr_at = G + jn_len + s_set[1] + j_len; end_at = clr_at + s_clr[1]
            body = [cat(op(0x07), (U32(clr_at), 4), L('Set')), s_set, cat(op(0x06), (U32(end_at), 4)), s_clr]
        elif fn == 'SRV_FollowNPC':  # roda de comandos dos seguidores: UID vem do GUID replicado do NPC
            GUIDP = (I32(1) + fname('GUID') + I32(imp('BlueprintGeneratedClass', 'BP_HumanQuest_Base_C')), 8)
            g = cat(op(0x01), GUIDP); guid = cat(op(0x19), L('NPC'), (U32(g[1]), 4), GUIDP, g)
            data = context(subsys, final(NAT['GetNPCDataByUID'], guid, L('Found')))
            body = [context(subsys, final(NAT[target], data, L('Cmd'), L('B1'), L('B2')))]
        elif fn == 'SRV_NPCEquip':
            s_eq = context(L('NPC'), virtual('EquipItemByIndex', L('Index')))
            s_un = context(L('NPC'), virtual('UnequipByIndex', L('Index'), L('Destroyed')))
            eq_at = G + 1 + 4 + L('Unequip')[1] + s_un[1] + 5; end_at = eq_at + s_eq[1]
            body = [cat(op(0x07), (U32(eq_at), 4), L('Unequip')), s_un, cat(op(0x06), (U32(end_at), 4)), s_eq]
        elif fn == 'SRV_SyncNPC':
            def LP(n): return (I32(1) + fname(n) + I32(me), 8)
            def mem(field, expr): return cat(op(0x42), (I32(1) + fname(field) + I32(S_NPCDATA), 8), expr)
            def lib(obj, f, *xs): return context(objconst(obj), final(LIBF[f], *xs))
            body = [cat(op(0x0F), LP('Data'), L('Data'), context(subsys, final(NAT['GetNPCDataByUID'], L('UID'), L('Found')), LP('Data'))),
                    lib(O_SETLIB, 'Set_ToArray', mem('PossibleTasks', L('Data')), L('Tasks')),
                    lib(O_SETLIB, 'Set_ToArray', mem('FollowCommands', L('Data')), L('Follow')),
                    lib(O_MAPLIB, 'Map_Keys', mem('Params', L('Data')), L('PKeys')),
                    lib(O_MAPLIB, 'Map_Values', mem('Params', L('Data')), L('PVals')),
                    cat(op(0x1C), objref(base_ec + list(RPCS).index('CLIENT_NPCSync') + 1), L('NPC'), L('Data'), L('Tasks'), L('Follow'), L('PKeys'), L('PVals'), op(0x16))]
        elif fn == 'CLIENT_NPCSync':
            def LP(n): return (I32(1) + fname(n) + I32(me), 8)
            NPCDATA = (I32(1) + fname('NPCData') + I32(C_NPC), 8)
            def npcf(field):  # NPC->NPCData.<field>
                inner = cat(op(0x01), NPCDATA)
                return cat(op(0x42), (I32(1) + fname(field) + I32(S_NPCDATA), 8), cat(op(0x19), L('NPC'), (U32(inner[1]), 4), NPCDATA, inner))
            def lib(obj, f, *xs): return context(objconst(obj), final(LIBF[f], *xs))
            def mathc(f, *xs): return callmath(LIBF[f], *xs)
            def intc(v): return cat(op(0x1D), (I32(v), 4))
            # NPCData completo do servidor (o cliente nao inicializa recrutaveis); TSet/TMap vem nos arrays
            npcd = cat(op(0x01), NPCDATA)
            setdata = cat(op(0x0F), NPCDATA, cat(op(0x19), L('NPC'), (U32(npcd[1]), 4), NPCDATA, npcd), L('Data'))
            pre = [setdata, lib(O_SETLIB, 'Set_Clear', npcf('PossibleTasks')), lib(O_SETLIB, 'Set_AddItems', npcf('PossibleTasks'), L('Tasks')),
                   lib(O_SETLIB, 'Set_Clear', npcf('FollowCommands')), lib(O_SETLIB, 'Set_AddItems', npcf('FollowCommands'), L('Follow')),
                   lib(O_MAPLIB, 'Map_Clear', npcf('Params')), cat(op(0x0F), LP('I'), L('I'), intc(0))]
            loop_at = sum(x[1] for x in pre)
            cond = mathc('Less_IntInt', L('I'), lib(O_ARRLIB, 'Array_Length', L('PKeys')))
            inner = [lib(O_ARRLIB, 'Array_Get', L('PKeys'), L('I'), L('K')), lib(O_ARRLIB, 'Array_Get', L('PVals'), L('I'), L('V')),
                     lib(O_MAPLIB, 'Map_Add', npcf('Params'), L('K'), L('V')),
                     cat(op(0x0F), LP('I'), L('I'), mathc('Add_IntInt', L('I'), intc(1)))]
            jmp_len = 1 + 4 + cond[1]
            end_at = loop_at + jmp_len + sum(x[1] for x in inner) + 5
            # redesenha as traits do dialogo aberto (UI_HMZQuest registrado em SyncUI pelo CheckRecruit)
            SYNCUI = (I32(1) + fname('SyncUI') + I32(CLS + 1), 8)
            ui = cat(op(0x01), SYNCUI)
            refresh = context(ui, virtual('AddTraits'))
            jn = cat(op(0x07), (U32(end_at + 1 + 4 + callmath(F_ISVALID, ui)[1] + refresh[1]), 4), callmath(F_ISVALID, ui))
            body = pre + [cat(op(0x07), (U32(end_at), 4), cond)] + inner + [cat(op(0x06), (U32(loop_at), 4)), jn, refresh]
        if guarded:
            body_mem = sum(x[1] for x in body)
            body = [cat(op(0x07), (U32(G + body_mem), 4), islocal)] + body
        script = cat(*body, op(0x04), op(0x0B), op(0x53))
        props = [typed(n, t, 0x94) for n, t in params] + [typed(n, t, 0) for n, t in locs]
        blob = fname('None') + I32(0) + I32(0) + I32(0) + I32(len(props)) + b''.join(props)
        blob += I32(script[1]) + I32(len(script[0])) + script[0]
        ff = 0x0D0000C0 if fn.startswith('CLIENT_') else 0x0C2000C0
        blob += U32(ff) + b'\0\0' + I32(0) + I32(0)  # Net|NetReliable|NetServer|BlueprintCallable|BlueprintEvent
        idx = p.add_export(TPL, fn, CLS + 1, blob, ([], [me], [], [CLS + 1]))
        assert idx == me; new_idx.append(me)
        print(f'{fn}: export {me}, script {len(script[0])} disco / {script[1]} mem')

    # classe: Children, FuncMap e dependencias
    cb = bytearray(p.blobs[CLS])
    q = 74; n = struct.unpack_from('<i', cb, q)[0]
    kids = [struct.unpack_from('<i', cb, q + 4 + 4 * i)[0] for i in range(n)]
    assert all(1 <= x <= base_ec for x in kids)
    cb[q + 4 + 4 * n:q + 4 + 4 * n] = b''.join(I32(x) for x in new_idx); struct.pack_into('<i', cb, q, n + len(new_idx))
    fm = None
    for z in range(q + 4 + 4 * (n + len(new_idx)), len(cb) - 4):
        if struct.unpack_from('<i', cb, z)[0] == n and z + 4 + 12 * n <= len(cb) and all(
                struct.unpack_from('<i', cb, z + 12 + 12 * k)[0] in kids for k in range(n)):
            fm = z; break
    assert fm, 'FuncMap nao encontrado'
    pairs = b''.join(fname(fn) + I32(i) for fn, i in zip(RPCS, new_idx))
    cb[fm + 4 + 12 * n:fm + 4 + 12 * n] = pairs; struct.pack_into('<i', cb, fm, n + len(new_idx))
    p.blobs[CLS] = bytes(cb)
    sbs, cbs, sbc, cbc = p.deps[CLS]; p.set_deps(CLS, (sbs, cbs + new_idx, sbc, cbc))
    os.makedirs(outdir, exist_ok=True)
    full = p.save(os.path.join(outdir, 'BP_HMZQuestComp.uasset'), os.path.join(outdir, 'BP_HMZQuestComp.uexp'))
    open(os.path.join(outdir, 'BP_HMZQuestComp.full'), 'wb').write(full)
    print('ok', len(full))

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
