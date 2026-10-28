# Mostra/altera PropertyFlags de propriedades de um export (ex.: classe BP). Uso:
#   propflags.py asset.bin ExportName Prop1,Prop2 [--set-net saida.bin]
import sys, struct, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset import Asset
a = Asset(sys.argv[1]); d = bytearray(a.d); exp = [e for e in a.exports if e['name'] == sys.argv[2]][0]
lo, hi = exp['off'], exp['off'] + exp['size']; idx = {n: i for i, n in enumerate(a.names)}
CPF_Net = 0x20
for pname in sys.argv[3].split(','):
    key = struct.pack('<ii', idx[pname], 0); q = d.find(key, lo, hi); hits = 0
    while q >= 0:
        tname = a.fn(*struct.unpack_from('<ii', d, q - 8))
        if tname.endswith('Property'):
            pf = struct.unpack_from('<Q', d, q + 20)[0]
            print(f'{pname} ({tname}) @{q}: flags 0x{pf:x} net={bool(pf & CPF_Net)}')
            if '--set-net' in sys.argv and hits == 0:
                struct.pack_into('<Q', d, q + 20, pf | CPF_Net); print('   -> 0x%x' % (pf | CPF_Net))
            hits += 1
        q = d.find(key, q + 1, hi)
if '--set-net' in sys.argv: open(sys.argv[sys.argv.index('--set-net') + 1], 'wb').write(d); print('salvo')
