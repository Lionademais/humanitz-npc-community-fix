# Desmonta todas as funcoes de um asset para uma pasta
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset import Asset; from kismet import Dis, find_script
a = Asset(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True); bad = []
for i, e in enumerate(a.exports):
    if a.obj(e['cls']) != '/Script/CoreUObject.Function': continue
    st = find_script(a, e)
    if not st: bad.append(e['name']); continue
    lines = Dis(a, *st).run()
    if any('!!' in x for _, _, x in lines): bad.append(e['name'] + '(!!)')
    with open(os.path.join(out, e['name'].replace('/', '_') + '.txt'), 'w') as f:
        for p, m, x in lines: f.write(f'{p:7d} m{m:5d}  {x}\n')
print('funcoes com problema:', bad)
