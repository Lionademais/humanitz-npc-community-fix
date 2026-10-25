HumanitZ - NPC Community Dedicated Fix - Dedicated Server
==========================================================

PORTUGUES
---------
Faz o recrutamento e o gerenciamento de NPCs (Comunidade, versao 1.1) funcionarem em servidor dedicado.
O servidor e a fonte da verdade. Os jogadores so precisam do mod de cliente (um pak, instalavel pelo Vortex).

O servidor precisa de duas coisas: o pak e uma correcao que habilita o subsistema nativo de comunidade
(HZCommunityNPCSubSys), que o jogo nao cria em servidor dedicado. E ele quem simula tarefas, fome e viagens e salva
os membros.

PASSO 1 - Copiar os arquivos (servidor parado)
 Extraia o zip na pasta raiz do servidor (a que contem a pasta HumanitZServer). Cada arquivo cai no lugar certo:
   HumanitZServer/Content/Paks/NPCCommunityFix_Server_P.pak     o mod
   HumanitZServer/Binaries/Linux/hzcommfix.so                   correcao para Linux
   HumanitZServer/Binaries/Win64/humanitz_npc_patcher.ps1       correcao para Windows
   extras/                                                      alternativa e codigo-fonte (opcional)

PASSO 2 - Ativar a correcao (escolha a do seu sistema)
 LINUX (recomendado): biblioteca hzcommfix.so via LD_PRELOAD
   Inicie o servidor com LD_PRELOAD apontando para o arquivo (caminho absoluto), por exemplo:
     LD_PRELOAD=/caminho/HumanitZServer/Binaries/Linux/hzcommfix.so ./HumanitZServer.sh -port=7777 ...
   AMP (CubeCoders): pare a instancia e, no GenericModule.kvp da instancia, acrescente em App.EnvironmentVariables:
     "LD_PRELOAD":"/caminho/da/instancia/humanitz/2728330/HumanitZServer/Binaries/Linux/hzcommfix.so"
   A correcao e feita na memoria ao iniciar: o executavel continua original e atualizacoes do jogo nao a desfazem.
   Confirmacao: a saida do servidor mostra "[hzcommfix] subsistema de comunidade habilitado no servidor dedicado"
   (no AMP a linha nao aparece no console, mas fica nos logs da instancia, pasta AMP_Logs).

 WINDOWS: humanitz_npc_patcher.ps1 (PowerShell, ja vem no Windows; nao precisa instalar nada)
   Na pasta HumanitZServer\Binaries\Win64, clique com o botao direito em humanitz_npc_patcher.ps1 ->
   "Executar com o PowerShell". Ele altera 2 bytes no HumanitZServer-Win64-Shipping.exe (cria backup .bak).
   Rodando de novo com o patch aplicado, ele oferece restaurar o original.
   Atualizacoes do jogo substituem o executavel: rode de novo depois de cada atualizacao.

 LINUX SEM LD_PRELOAD (alternativa): python3 extras/humanitz_npc_patcher.py HumanitZServer/Binaries/Linux/HumanitZServer-Linux-Shipping
   (cria .bak; desfazer com --restore; rodar de novo apos cada atualizacao)

PASSO 3 - Iniciar o servidor.

Observacoes
- Os patchers sao texto (podem ser lidos antes de rodar) e acham o ponto pelo conteudo, recusando versoes
  desconhecidas. Se o jogo mudar essa funcao, nada e alterado ate sair uma nova versao do mod.
- Codigo-fonte da biblioteca: extras/hzcommfix.c (compilar: gcc -O2 -shared -fPIC -o hzcommfix.so extras/hzcommfix.c)
- Comunidades criadas antes do mod em servidor dedicado nunca foram registradas: desmonte a Base da Comunidade e
  construa de novo depois de instalar.
- Desinstalar: remova o pak e o LD_PRELOAD (ou restaure o executavel pelo patcher / valide os arquivos do servidor).
- Servidor e todos os jogadores precisam da mesma versao do mod.

ENGLISH
-------
Makes NPC recruitment and management (Community, version 1.1) work on dedicated servers.
The server is authoritative. Players only need the client mod (a single pak, installable with Vortex).

The server needs two things: the pak and a fix that enables the native community subsystem (HZCommunityNPCSubSys),
which the game does not create on dedicated servers. It simulates tasks, hunger and travel and saves the members.

STEP 1 - Copy the files (server stopped)
 Extract the zip into the server's root folder (the one containing the HumanitZServer folder). Every file lands in
 the right place:
   HumanitZServer/Content/Paks/NPCCommunityFix_Server_P.pak     the mod
   HumanitZServer/Binaries/Linux/hzcommfix.so                   Linux fix
   HumanitZServer/Binaries/Win64/humanitz_npc_patcher.ps1       Windows fix
   extras/                                                      alternative and source code (optional)

STEP 2 - Enable the fix (pick your OS)
 LINUX (recommended): hzcommfix.so library via LD_PRELOAD
   Start the server with LD_PRELOAD pointing to the file (absolute path), e.g.:
     LD_PRELOAD=/path/HumanitZServer/Binaries/Linux/hzcommfix.so ./HumanitZServer.sh -port=7777 ...
   AMP (CubeCoders): stop the instance and, in the instance's GenericModule.kvp, add to App.EnvironmentVariables:
     "LD_PRELOAD":"/path/to/instance/humanitz/2728330/HumanitZServer/Binaries/Linux/hzcommfix.so"
   The fix is applied in memory at startup: the executable stays original and game updates do not undo it.
   Check: the server output shows "[hzcommfix] subsistema de comunidade habilitado no servidor dedicado"
   (on AMP the line is not shown in the console, but it is written to the instance logs, AMP_Logs folder).

 WINDOWS: humanitz_npc_patcher.ps1 (PowerShell, built into Windows; nothing to install)
   In HumanitZServer\Binaries\Win64, right-click humanitz_npc_patcher.ps1 -> "Run with PowerShell".
   It changes 2 bytes in HumanitZServer-Win64-Shipping.exe (keeps a .bak backup).
   Running it again when already applied offers to restore the original.
   Game updates replace the executable: run it again after every update.

 LINUX WITHOUT LD_PRELOAD (alternative): python3 extras/humanitz_npc_patcher.py HumanitZServer/Binaries/Linux/HumanitZServer-Linux-Shipping
   (keeps .bak; undo with --restore; run again after every update)

STEP 3 - Start the server.

Notes
- The patchers are plain text (you can read them before running) and locate the code by content, refusing unknown
  versions. If the game changes this function, nothing is changed until a new mod version is released.
- Library source code: extras/hzcommfix.c (build: gcc -O2 -shared -fPIC -o hzcommfix.so extras/hzcommfix.c)
- Communities created on a dedicated server before this mod were never registered: dismantle the Community Base
  and build it again after installing.
- Uninstall: remove the pak and the LD_PRELOAD (or restore the executable with the patcher / validate server files).
- The server and all players need the same mod version.
