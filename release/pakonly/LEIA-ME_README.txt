HumanitZ - NPC Mechanics on Dedicated Server (antes/formerly: NPC Community Dedicated Fix) - PAK-ONLY server 1.1.2 (no executable changes)
==========================================================================================================================================

PORTUGUES
---------
Faz o recrutamento e o gerenciamento de NPCs (Comunidade) funcionarem em servidor dedicado, SO com arquivos de pak.
Nao mexe no executavel do jogo: sem hzcommfix.so, sem LD_PRELOAD, sem patcher. Serve para servidor alugado em que o
painel so deixa enviar arquivos.

Qual escolher
- PAK-ONLY (este zip): servidor alugado, ou sem acesso ao executavel e a linha de inicializacao.
  Traz os bugs de tracos do jogo corrigidos, a comunidade continua vivendo sem jogador por perto e o relogio da
  comunidade segue a duracao do dia do servidor (DayDur/NightDur).
- NATIVA (zip NPCCommunityFix_DedicatedServer): servidor proprio, VPS ou AMP, em que voce controla a inicializacao.
  Usa o codigo do proprio jogo, igual a ele (inclusive nos bugs), e inclui a protecao do mundo do hzcommfix.so.
- Instale SO UMA das duas.

Jogadores
- O cliente e o MESMO das duas opcoes: NPCCommunityFix_Client 1.0.8 (um pak, pelo Vortex ou em Paks\~mods).
  Servidor pak-only 1.1.2 ou nativo 1.0.10, cliente 1.0.8: o numero do servidor sobe quando so ele muda.

Este zip vale para UM sistema. Use o do seu servidor:
  NPCMechanics_PakOnly_LinuxServer_v*.zip     servidor dedicado Linux
  NPCMechanics_PakOnly_WindowsServer_v*.zip   servidor dedicado Windows

Instalacao (formato IoStore: tres arquivos que andam juntos)
 1. Pare o servidor.
 2. Se a versao NATIVA estava instalada, tire tudo dela antes:
    - apague HumanitZServer/Content/Paks/NPCCommunityFix_Server_P.pak, .ucas, .utoc e .sig;
    - Linux: tire o LD_PRELOAD do hzcommfix.so da inicializacao (no AMP, do GenericModule.kvp). Com o hzcommfix.so
      ligado e sem o pak nativo, o servidor se recusa a subir ("mod de servidor ausente");
    - Windows: volte o executavel original (rode humanitz_npc_patcher.ps1 de novo e aceite restaurar, ou valide os
      arquivos do servidor). Com o executavel corrigido o servidor funciona, mas como a versao nativa.
 3. Extraia o zip na pasta raiz do servidor (a que contem a pasta HumanitZServer). Os arquivos caem em:
      HumanitZServer/Content/Paks/NPCMechanics_PakOnly_Server_P.pak
      HumanitZServer/Content/Paks/NPCMechanics_PakOnly_Server_P.ucas
      HumanitZServer/Content/Paks/NPCMechanics_PakOnly_Server_P.utoc
    Painel de hospedagem: envie os tres para HumanitZServer/Content/Paks. Os tres juntos, com o mesmo nome:
    sem o .ucas e o .utoc o jogo ignora o .pak.
 4. Ligue o servidor.
 5. Confirmacao: o log do servidor (HumanitZServer/Saved/Logs/HumanitZServer.log) mostra uma linha
      LogKaiHelper: NPCM hora=<hora> vel=<velocidade> dt=<passo>
    a cada hora do jogo.

Bom saber
- Faca backup dos saves antes. A versao pak-only nao tem a protecao do mundo do hzcommfix.so (trava, cofre e reparo).
- Nada extra e gravado no save: da para voltar a versao nativa sem perder nada.
- Feito para os servidores de 30/10/2026 (Linux 26333826, Windows 26335264). Depois de cada atualizacao do jogo,
  espere a versao do mod para o novo build.
- Desinstalar: apague os tres arquivos NPCMechanics_PakOnly_Server_P.*.

ENGLISH
-------
Makes NPC recruitment and management (Community) work on dedicated servers using ONLY pak files.
The game executable is not touched: no hzcommfix.so, no LD_PRELOAD, no patcher. Made for rented servers whose panel
only lets you upload files.

Which one to pick
- PAK-ONLY (this zip): rented server, or no access to the executable and the startup command line.
  Ships with the game's trait bugs fixed, communities keep living while no player is around, and the community clock
  follows the server's day length (DayDur/NightDur).
- NATIVE (NPCCommunityFix_DedicatedServer zip): your own machine, VPS or AMP, where you control the startup.
  Runs the game's own code, exactly like the game (bugs included), and includes the world protection of hzcommfix.so.
- Install ONLY ONE of them.

Players
- The client is the SAME for both options: NPCCommunityFix_Client 1.0.8 (one pak, via Vortex or in Paks\~mods).
  Pak-only server 1.1.2 or native server 1.0.10, client 1.0.8: the server number goes up when only the server changes.

This zip is for ONE operating system. Use the one that matches your server:
  NPCMechanics_PakOnly_LinuxServer_v*.zip     Linux dedicated server
  NPCMechanics_PakOnly_WindowsServer_v*.zip   Windows dedicated server

Install (IoStore format: three files that always go together)
 1. Stop the server.
 2. If the NATIVE option was installed, remove it first:
    - delete HumanitZServer/Content/Paks/NPCCommunityFix_Server_P.pak, .ucas, .utoc and .sig;
    - Linux: remove the hzcommfix.so LD_PRELOAD from the startup (on AMP, from GenericModule.kvp). With hzcommfix.so
      loaded and no native pak, the server refuses to start ("mod de servidor ausente");
    - Windows: restore the original executable (run humanitz_npc_patcher.ps1 again and accept the restore, or
      validate the server files). With the patched executable the server works, but behaves like the native option.
 3. Extract the zip into the server's root folder (the one containing the HumanitZServer folder). The files land in:
      HumanitZServer/Content/Paks/NPCMechanics_PakOnly_Server_P.pak
      HumanitZServer/Content/Paks/NPCMechanics_PakOnly_Server_P.ucas
      HumanitZServer/Content/Paks/NPCMechanics_PakOnly_Server_P.utoc
    Hosting panel: upload the three files to HumanitZServer/Content/Paks. Keep all three together with the same name:
    without the .ucas and .utoc the game ignores the .pak.
 4. Start the server.
 5. Check: the server log (HumanitZServer/Saved/Logs/HumanitZServer.log) shows a line
      LogKaiHelper: NPCM hora=<hour> vel=<speed> dt=<step>
    every in-game hour.

Good to know
- Back up your saves first. The pak-only option does not have the world protection of hzcommfix.so (lock, vault
  and repair).
- Nothing extra is written to your save: you can switch back to the native option without losing anything.
- Built for the servers of 30 Oct 2026 (Linux 26333826, Windows 26335264). After every game update, wait for the mod
  version for the new build.
- Uninstall: delete the three NPCMechanics_PakOnly_Server_P.* files.
