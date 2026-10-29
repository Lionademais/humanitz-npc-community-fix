#!/bin/bash
# Monta os zips de publicacao (Nexus/Vortex) a partir de paks/ (build.sh) e shim/.
# Uso: release.sh <versao>             -> teste/     (versao em desenvolvimento; apaga zips anteriores de teste/)
#      release.sh <versao> --publicar  -> versoes/   (versao lancada; substitui a anterior, o historico fica no GitHub)
# Nomes (sempre iguais): NPCCommunityFix_Client_v<versao>.zip e NPCCommunityFix_DedicatedServer_v<versao>.zip
#   Client: so o pak, na raiz (o Vortex instala em Paks\~mods).
#   DedicatedServer: extraido na raiz do servidor: pak, hzcommfix.so (Linux), patcher .ps1 (Windows) e extras/
#   (patcher .py e codigo-fonte). Sem .bat nem .exe: a quarentena do Nexus reteve uma versao com .bat chamando PowerShell.
set -e
cd "$(dirname "$0")"; V=${1:?informe a versao, ex.: 1.0.3}; R=release; S=$R/servidor
if [ "$2" = "--publicar" ]; then D=versoes; else D=teste; fi
mkdir -p $D; rm -f $D/NPCCommunityFix_*.zip
cp paks/HumanitZ_CommunityFix_P.pak $R/cliente/NPCCommunityFix_Client_P.pak
mkdir -p $S/HumanitZServer/Content/Paks $S/HumanitZServer/Binaries/Linux $S/extras
cp paks/zz_CommunityFix_P.pak $S/HumanitZServer/Content/Paks/NPCCommunityFix_Server_P.pak
cp shim/hzcommfix.so $S/HumanitZServer/Binaries/Linux/hzcommfix.so
cp shim/hzcommfix.c $S/extras/hzcommfix.c
(cd $R/cliente && zip -q -X -9 ../../$D/NPCCommunityFix_Client_v$V.zip NPCCommunityFix_Client_P.pak LEIA-ME_README.txt)
(cd $S && zip -q -X -9 -r ../../$D/NPCCommunityFix_DedicatedServer_v$V.zip HumanitZServer extras LEIA-ME_README.txt)
ls -la $D; sha256sum $D/*.zip
