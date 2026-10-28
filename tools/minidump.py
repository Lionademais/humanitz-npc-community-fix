# Le um UE4Minidump.dmp (Windows): excecao, registradores, modulos e varredura da pilha por enderecos do .exe.
# Uso: minidump.py arquivo.dmp  (depois mapear RVAs para funcoes via .pdata e desmontar com Ghidra, ver skill)
import struct,sys
d=open(sys.argv[1],'rb').read()
sig,ver,n,dirrva=struct.unpack_from('<IIII',d,0)
streams={}
for i in range(n):
    t,sz,rva=struct.unpack_from('<III',d,dirrva+12*i); streams.setdefault(t,[]).append((sz,rva))
def ustr(rva):
    l=struct.unpack_from('<I',d,rva)[0]; return d[rva+4:rva+4+l].decode('utf-16-le')
mods=[]
sz,rva=streams[4][0]; cnt=struct.unpack_from('<I',d,rva)[0]
for i in range(cnt):
    o=rva+4+108*i; base,size,chk,ts,namerva=struct.unpack_from('<QIIII',d,o); mods.append((base,size,ts,ustr(namerva)))
def mod_of(a):
    for b,s,ts,nm in mods:
        if b<=a<b+s: return nm.split('\\')[-1], a-b
    return None
sz,rva=streams[6][0]
tid,_=struct.unpack_from('<II',d,rva); code,flags,rec,addr,np_=struct.unpack_from('<IIQQI',d,rva+8)
info=struct.unpack_from('<15Q',d,rva+8+4+4+8+8+4+4)
ctxsz,ctxrva=struct.unpack_from('<II',d,rva+8+152)
print('tid',tid,'code',hex(code),'addr',hex(addr),mod_of(addr),'info',[hex(x) for x in info[:2]])
regs=['Rax','Rcx','Rdx','Rbx','Rsp','Rbp','Rsi','Rdi','R8','R9','R10','R11','R12','R13','R14','R15','Rip']
vals=struct.unpack_from('<17Q',d,ctxrva+0x78)
R=dict(zip(regs,vals)); print({k:hex(v) for k,v in R.items()})
exe=[m for m in mods if m[3].lower().endswith('shipping.exe')]; print('exe',[(hex(b),hex(s),ts,nm) for b,s,ts,nm in exe])
# memoria
mem=[]
if 9 in streams:
    sz,rva=streams[9][0]; cnt,base=struct.unpack_from('<QQ',d,rva); off=base
    for i in range(cnt):
        st,ds=struct.unpack_from('<QQ',d,rva+16+16*i); mem.append((st,ds,off)); off+=ds
if 5 in streams:
    sz,rva=streams[5][0]; cnt=struct.unpack_from('<I',d,rva)[0]
    for i in range(cnt):
        st,ds,mrva=struct.unpack_from('<QII',d,rva+4+16*i); mem.append((st,ds,mrva))
def rd(a,n):
    for st,ds,off in mem:
        if st<=a and a+n<=st+ds: return d[off+a-st:off+a-st+n]
rsp=R['Rsp']; print('stack scan:')
k=0
for i in range(0,0x2000,8):
    b=rd(rsp+i,8)
    if not b: break
    v=struct.unpack('<Q',b)[0]; mo=mod_of(v)
    if mo and mo[0].lower().endswith('.exe'):
        print(hex(rsp+i), mo[0], hex(mo[1])); k+=1
        if k>40: break
