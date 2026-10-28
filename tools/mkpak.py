# Gera um .pak UE4 versao 7 (sem compressao, sem criptografia). Uso: mkpak.py saida.pak mountpoint caminho_no_pak=arquivo ...
import struct, hashlib, sys
out, mount = sys.argv[1], sys.argv[2]
def fstr(s): b = s.encode() + b'\0'; return struct.pack('<i', len(b)) + b
def entry(off, data): return struct.pack('<qqqi', off, len(data), len(data), 0) + hashlib.sha1(data).digest() + struct.pack('<BI', 0, 0)
body = bytearray(); idx = []
for arg in sys.argv[3:]:
    name, src = arg.split('=', 1); data = open(src, 'rb').read()
    off = len(body); body += entry(0, data) + data; idx.append((name, off, data))
index = fstr(mount) + struct.pack('<i', len(idx))
for name, off, data in idx: index += fstr(name) + entry(off, data)
trailer = b'\0' * 16 + b'\0' + struct.pack('<Iiqq', 0x5A6F12E1, 7, len(body), len(index)) + hashlib.sha1(index).digest()
open(out, 'wb').write(bytes(body) + index + trailer)
print('ok', out, len(idx), 'arquivos', len(body) + len(index) + len(trailer), 'bytes')
