# Arvore de layout de um widget (Parent/Content dos slots, alinhamento, padding, SizeBox, textos): uitree.py asset
import sys, subprocess, re
out = subprocess.run([sys.executable, '-I', sys.argv[0].replace('uitree.py', 'uitags.py'), sys.argv[1]], capture_output=True, text=True).stdout
blocks = re.split(r'^== ', out, flags=re.M)[1:]
info = {}; slots = []
for b in blocks:
    head, *lines = b.split('\n'); name, cls = head.split()[0], head.split()[1]
    d = {}
    for l in lines:
        m = re.match(r'\s*(\w+)\[0\] \S+ ?\S* = (.*)', l)
        if m: d.setdefault(m.group(1), m.group(2))
    pad = [re.search(r'(Left|Top|Right|Bottom)\[0\] FloatProperty  = (\S+)', l) for l in lines]
    d['pad'] = {m.group(1): round(float(m.group(2))) for m in pad if m}
    info.setdefault(name, []).append((cls.split('.')[-1], d))
    if 'Slot' in cls and 'Content' in d: slots.append((d.get('Parent'), d['Content'], cls.split('.')[-1], d))
kids = {}
for par, c, cls, d in slots: kids.setdefault(par, []).append((c, cls, d))
def desc(n):
    for cls, d in info.get(n, []):
        if 'Slot' in cls: continue
        x = [cls]
        for k in ('WidthOverride', 'HeightOverride', 'MinDesiredWidth', 'MaxDesiredWidth', 'ImageSize'):
            if k in d: x.append(f'{k}={d[k][:12]}')
        if 'Text' in d: t = re.findall(r"[A-Za-z][A-Za-z :/'-]{2,}", d['Text']); x.append(repr(t[-1] if t else ''))
        return ' '.join(x)
    return '?'
def show(n, ind=0, seen=set()):
    for c, cls, d in kids.get(n, []):
        al = ' '.join(f"{k[0]}{d[k].split('_')[-1]}" for k in ('HorizontalAlignment', 'VerticalAlignment') if k in d)
        sz = d.get('SizeRule', '')
        print('  ' * ind + f'{c}: {desc(c)} [{cls} {al} pad={d["pad"] or ""} {sz}]')
        if c not in seen: seen.add(c); show(c, ind + 1)
roots = [p for p in kids if not any(p == c for _, c, _, _ in slots)]
for r in roots: print(r, desc(r)); show(r, 1)
