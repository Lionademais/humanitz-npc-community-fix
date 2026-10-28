# Confere se toda funcao nativa (/Script/...) importada pelos assets existe como nome registrado no executavel.
# Import de UFUNCTION inexistente vira nulo e o jogo cai em UObject::CallFunction (leitura em +0xb0).
# Uso: check_imports.py executavel asset.full...
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset import Asset
exe = open(sys.argv[1], 'rb').read(); ruim = 0
for f in sys.argv[2:]:
    a = Asset(f); imps = a.imports; bad = []
    for c, o, n in imps:
        if c != 'Function' or o >= 0: continue
        oc = imps[-o - 1]; pk = imps[-oc[1] - 1][2] if oc[1] < 0 else ''
        if pk.startswith('/Script/') and exe.find(n.encode() + b'\0') < 0 and exe.find(n.encode('utf-16-le') + b'\0\0') < 0:
            bad.append(f'{oc[2]}.{n}')
    ruim += len(bad); print(os.path.basename(f), 'ok' if not bad else f'FALTANDO: {bad}')
sys.exit(1 if ruim else 0)
