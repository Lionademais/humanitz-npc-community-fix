#!/bin/bash
# Recria os paks do mod de comunidade/NPCs do HumanitZ a partir dos assets originais (pasta originais/).
# Saida: paks/zz_CommunityFix_P.pak (servidor) e paks/HumanitZ_CommunityFix_P.pak (cliente).
# Cliente: so o pak (o subsistema de comunidade e criado pelo BP_HMZQuestComp.CommSubFix, ver build_commsub.py).
# Servidor dedicado: requer a correcao nativa do ShouldCreateSubsystem (ver memoria humanitz-exe-patches).
set -e
cd "$(dirname "$0")"; T=tools; O=originais; B=build; rm -rf $B; mkdir -p $B paks
py() { python3 -I "$@"; }
# ---- servidor
py $T/patch_cbuild.py $O/C-Building_srv.bin $B/srv_cb
py $T/patch_dismantle.py $B/srv_cb/C-Building.full $O/BPK_CommunityBaseLevel1_srv.bin $B/srv
py $T/patch_basename.py $B/srv/BPK_CommunityBaseLevel1.full $B/srv
py $T/patch_gs.py $O/BP_GameStateBase_srv.bin $B/srv
py $T/patch_savecomm.py $O/BP_GameModeSave_srv.bin $B/srv
py $T/flipnet.py $O/BP_BaseInteractActor_srv.bin $B/srv BP_BaseInteractActor BP_BaseInteractActor_C ActorName:TextProperty:UpdateName
py $T/build_sync.py $O/quest_srv.bin $B/srv_sync --server
py $T/build_rpcs.py $B/srv_sync/BP_HMZQuestComp.full $B/srv_rpcs
py $T/build_commsub.py $B/srv_rpcs/BP_HMZQuestComp.full $B/srv_sub
py $T/swap_subsys.py $B/srv_sub/BP_HMZQuestComp.full $B/srv BP_HMZQuestComp
# ---- cliente
py $T/build_sync.py $O/quest_cli.bin $B/cli_sync
py $T/build_rpcs.py $B/cli_sync/BP_HMZQuestComp.full $B/cli_rpcs
py $T/build_commsub.py $B/cli_rpcs/BP_HMZQuestComp.full $B/cli_sub
py $T/build_uiquest.py $O/UI_HMZQuest_cli.bin $B/cli_pre
py $T/flipnet.py $O/BP_BaseInteractActor_cli.bin $B/cli BP_BaseInteractActor BP_BaseInteractActor_C ActorName:TextProperty:UpdateName
py $T/patch_base.py $O/BPK_CommunityBaseLevel1_cli.bin $B/cli_pre 43732
py $T/build_charbase.py $O/BP_CharacterBase_cli.bin $B/cli_pre
# chamadas ao subsistema -> CommSubFix (cliente sem patch no executavel)
py $T/patch_showmsg.py $B/cli_sub/BP_HMZQuestComp.full $B/cli_msg
py $T/swap_subsys.py $B/cli_msg/BP_HMZQuestComp.full $B/cli BP_HMZQuestComp
for x in UI_HMZQuest BPK_CommunityBaseLevel1 BP_CharacterBase; do py $T/swap_subsys.py $B/cli_pre/$x.full $B/cli $x; done
for x in UI_CommunityTab UI_CommunityMemberInfo UI_PreTaskInfo; do py $T/swap_subsys.py $O/${x}_cli.bin $B/cli $x; done
# ---- paks
I=TSS_Game/KaiWorldEffects/InteractActor; M=TSS_Game/Blueprints/Objective_System/System; Q=TSS_Game/KaiAIMapTest/KaiHumanAI/Quest; G=TSS_Game/Blueprints/System; C=BuildingSystem/Blueprints
W=$Q/QuestPreset/Random/Recruit/Widgets
pk() { local root=$1 dir=$2 asset=$3; shift 3; for e in uasset uexp; do echo "$root/Content/$dir/$asset.$e=$B/$1/$asset.$e"; done; }
py $T/mkpak.py paks/zz_CommunityFix_P.pak "../../../" $(pk HumanitZServer $C C-Building srv) $(pk HumanitZServer $Q BP_HMZQuestComp srv) \
   $(pk HumanitZServer $G BP_GameStateBase srv) $(pk HumanitZServer $I BP_BaseInteractActor srv) $(pk HumanitZServer $I/Child BPK_CommunityBaseLevel1 srv) \
   $(pk HumanitZServer $M BP_GameModeSave srv)
py $T/mkpak.py paks/HumanitZ_CommunityFix_P.pak "../../../" $(pk HumanitZ $Q BP_HMZQuestComp cli) $(pk HumanitZ $Q UI_HMZQuest cli) \
   $(pk HumanitZ $I BP_BaseInteractActor cli) $(pk HumanitZ $I/Child BPK_CommunityBaseLevel1 cli) $(pk HumanitZ $G BP_CharacterBase cli) \
   $(pk HumanitZ $W UI_CommunityTab cli) $(pk HumanitZ $W UI_CommunityMemberInfo cli) $(pk HumanitZ $W UI_PreTaskInfo cli)
sha1sum paks/*.pak
# ---- confere imports nativos contra os executaveis (UFUNCTION inexistente = import nulo = crash)
# caminhos dos executaveis em build.local.sh (nao versionado): HZ_SERVER_BIN=... HZ_CLIENT_EXE=...
[ -f build.local.sh ] && . ./build.local.sh; SRVBIN=${HZ_SERVER_BIN:-}; CLIEXE=${HZ_CLIENT_EXE:-}
[ -n "$SRVBIN" ] && [ -f "$SRVBIN" ] && py $T/check_imports.py $SRVBIN $B/srv/*.full >/dev/null && echo "imports servidor ok"
[ -n "$CLIEXE" ] && [ -f "$CLIEXE" ] && py $T/check_imports.py $CLIEXE $B/cli/*.full >/dev/null && echo "imports cliente ok"
