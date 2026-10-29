# Despeja as propriedades (tagged) dos exports de um asset: uitags.py asset [export...]
import sys, struct
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from uasset import Asset
a = Asset(sys.argv[1]); d = a.d
def fname(q): return a.fn(*struct.unpack_from('<ii', d, q))
def props(q, end, ind='  '):
    while q < end:
        n = fname(q); q += 8
        if n == 'None': return q
        t = fname(q); q += 8; size, idx = struct.unpack_from('<ii', d, q); q += 8; extra = ''
        if t == 'StructProperty': extra = fname(q); q += 8 + 16
        elif t == 'BoolProperty': extra = d[q]; q += 1
        elif t in ('ByteProperty', 'EnumProperty'): extra = fname(q); q += 8
        elif t in ('ArrayProperty', 'SetProperty'): extra = fname(q); q += 8
        elif t == 'MapProperty': extra = fname(q) + ',' + fname(q + 8); q += 16
        hg = d[q]; q += 1 + (16 if hg else 0)
        v = d[q:q + size]; val = ''
        if t == 'ObjectProperty': val = a.obj(struct.unpack_from('<i', v)[0])
        elif t == 'FloatProperty': val = struct.unpack_from('<f', v)[0]
        elif t == 'IntProperty': val = struct.unpack_from('<i', v)[0]
        elif t in ('ByteProperty', 'EnumProperty') and size == 8: val = fname(q)
        elif t == 'NameProperty': val = fname(q)
        elif t == 'StructProperty' and extra in ('Vector2D',): val = struct.unpack_from('<ff', v)
        elif False: pass
        elif t == 'TextProperty': val = v[-60:]
        print(f'{ind}{n}[{idx}] {t} {extra} = {val}')
        if t == 'StructProperty' and extra not in ('Vector2D', 'LinearColor', 'Vector', 'Guid', 'Color'):
            props(q, q + size, ind + '    ')
        q += size
    return q
for e in a.exports:
    if len(sys.argv) > 2 and e['name'] not in sys.argv[2:]: continue
    print('==', e['name'], a.obj(e['cls']), e['off'], e['size'])
    try: props(e['off'], e['off'] + e['size'])
    except Exception as ex: print('  erro', ex)
