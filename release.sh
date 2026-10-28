#!/bin/bash
# Monta os pacotes de publicacao (Nexus/Vortex) a partir de paks/ (build.sh) e shim/.
# Saida em release/dist:
#   NPCCommunityFix_Client_vX.zip           so o pak do cliente, na raiz (formato que o Vortex instala em Paks\~mods)
#   NPCCommunityFix_DedicatedServer_vX.zip  extraido na raiz do servidor: pak, hzcommfix.so (Linux), patcher .ps1
#                                           (Windows) e extras/ (patcher .py e codigo-fonte). Sem .bat nem .exe: a
#                                           quarentena automatica do Nexus reteve a versao com .bat chamando PowerShell.
set -e
cd "$(dirname "$0")"; V=${1:-1.0.0}; R=release; D=$R/dist; S=$R/servidor
rm -rf $D; mkdir -p $D
cp paks/HumanitZ_CommunityFix_P.pak $R/cliente/NPCCommunityFix_Client_P.pak
mkdir -p $S/HumanitZServer/Content/Paks $S/HumanitZServer/Binaries/Linux $S/extras
cp paks/zz_CommunityFix_P.pak $S/HumanitZServer/Content/Paks/NPCCommunityFix_Server_P.pak
cp shim/hzcommfix.so $S/HumanitZServer/Binaries/Linux/hzcommfix.so
cp shim/hzcommfix.c $S/extras/hzcommfix.c
(cd $R/cliente && zip -q -X -9 ../dist/NPCCommunityFix_Client_v$V.zip NPCCommunityFix_Client_P.pak LEIA-ME_README.txt)
(cd $S && zip -q -X -9 -r ../dist/NPCCommunityFix_DedicatedServer_v$V.zip HumanitZServer extras LEIA-ME_README.txt)
ls -la $D; sha256sum $D/*.zip
