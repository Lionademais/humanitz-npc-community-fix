#!/usr/bin/env python3
# HumanitZ - NPC Community Dedicated Fix - patcher do executavel
#
# O subsistema de comunidade de NPCs (HZCommunityNPCSubSys) so e criado pelo jogo no host/single-player.
# Este patcher altera 2-3 bytes em UHZCommunityNPCSubSys::ShouldCreateSubsystem para que ele tambem seja criado
# no servidor dedicado (o cliente nao precisa: o mod de cliente e so um pak). Busca por padrao, nao por endereco fixo.
#
# Uso:  python3 humanitz_npc_patcher.py <caminho do executavel>            aplica o patch (cria .bak)
#       python3 humanitz_npc_patcher.py --restore <caminho do executavel>  restaura o .bak
# Executaveis suportados:
#   HumanitZServer-Win64-Shipping.exe      (servidor dedicado Windows)
#   HumanitZServer-Linux-Shipping          (servidor dedicado Linux)
import os, re, shutil, sys

PATCHES = [
    ('servidor Windows', '40 53 48 83 EC 20 48 8B DA E8 ?? ?? ?? ?? 84 C0 74 0A 48 85 DB 74 05 E8 ?? ?? ?? ?? 32 C0 48 83 C4 20 5B C3', 16, 'EB 0C'),
    ('servidor Linux', '53 48 89 F3 E8 ?? ?? ?? ?? 48 85 DB 74 09 84 C0 74 05 E8 ?? ?? ?? ?? 31 C0 5B C3', 9, '5B C3 90'),
]

def regex(tokens):
    return re.compile(b''.join(b'.' if t == '??' else re.escape(bytes([int(t, 16)])) for t in tokens), re.S)

def patched_tokens(pat, off, new):
    t = pat.split(); n = new.split(); t[off:off + len(n)] = n; return t

def main(argv):
    restore = '--restore' in argv
    args = [a for a in argv if a != '--restore']
    if len(args) != 1:
        print('uso: humanitz_npc_patcher.py [--restore] <executavel>'); return 2
    exe = args[0]; bak = exe + '.bak'
    if not os.path.isfile(exe):
        print(f'ERRO: arquivo nao encontrado: {exe}'); return 1
    if restore:
        if not os.path.isfile(bak):
            print(f'ERRO: backup nao encontrado: {bak}'); return 1
        shutil.copy2(bak, exe); print(f'Restaurado a partir de {bak}'); return 0
    data = bytearray(open(exe, 'rb').read())
    for name, pat, off, new in PATCHES:
        if len(regex(patched_tokens(pat, off, new)).findall(data)) == 1:
            print(f'O patch ja esta aplicado ({name}). Nada a fazer.'); return 0
        hits = [m.start() for m in regex(pat.split()).finditer(data)]
        if len(hits) > 1:
            print(f'ERRO: padrao ambiguo ({name}, {len(hits)} ocorrencias). Nao alterado.'); return 1
        if len(hits) == 1:
            pos = hits[0] + off; nb = bytes(int(x, 16) for x in new.split())
            if not os.path.isfile(bak): shutil.copy2(exe, bak); print(f'Backup criado: {bak}')
            data[pos:pos + len(nb)] = nb
            tmp = exe + '.tmp'
            with open(tmp, 'wb') as f: f.write(data)
            shutil.copymode(exe, tmp); os.replace(tmp, exe)
            print(f'Patch aplicado ({name}) no offset 0x{pos:X}.'); return 0
    print('ERRO: padrao nao encontrado. Versao do jogo nao suportada por este patcher (o jogo pode ter sido atualizado).')
    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
