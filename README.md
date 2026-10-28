# NPC Mechanics on Dedicated Server (HumanitZ)

Full source code and build instructions for the HumanitZ mod **NPC Mechanics on Dedicated Server**
(internal name *NPC Community Dedicated Fix*). It makes the NPC recruitment and Community system of HumanitZ 1.1
work on dedicated servers, with the server as the single source of truth.

- **Current release: [1.0.2](https://github.com/Lionademais/humanitz-npc-community-fix/releases/tag/v1.0.2)**, for HumanitZ 1.1B
- Nexus Mods page: https://www.nexusmods.com/games/humanitz/mods/171
- Client and server must always run the **same mod version** (1.0.2 client requires 1.0.2 server and vice versa).

## What's new in 1.0.2

- **Save protection:** if the server starts without the native fix ("step 2"), community data is no longer erased
  from the save. It stays stored and comes back as soon as the fix is applied again.
- **Automatic repair of orphan bases:** a Community Base built or upgraded while step 2 was inactive used to have no
  community ("Unknown Community", recruiting did not work, NPCs said the camp was full). The server now recreates the
  missing community (matching the base level 1-4) when the owner is online, and shows the player a translated
  "Community restored" message.
- **Cleaner server log:** the "Replicated TMaps are not supported" error no longer repeats every 2 seconds.
- **Server README:** new section on keeping step 2 active after game, host panel or AMP updates.

Full history in the [Changelog](#changelog).

## Repository layout

| Path | What it is |
|---|---|
| `build.sh` | Rebuilds both paks from the game's original assets (`originals/`, not included). |
| `release.sh` | Packs the paks, the Linux library and the scripts into the two release zips. |
| `shim/hzcommfix.c` | Source of `hzcommfix.so`, the Linux server library (the only compiled binary in the mod). |
| `tools/` | Python tools (no external dependencies) that read and rebuild cooked UE 4.27 packages, assemble Kismet bytecode and write the paks. |
| `release/servidor/` | Files shipped in the server zip besides the pak and the library: `LEIA-ME_README.txt`, the Windows patcher (`HumanitZServer/Binaries/Win64/humanitz_npc_patcher.ps1`) and the Python patcher (`extras/humanitz_npc_patcher.py`). |
| `release/cliente/` | `LEIA-ME_README.txt` shipped in the client zip. |
| `SHA256SUMS.txt` | SHA-256 of the release zips and of every file inside them. |
| `.github/workflows/build.yml` | GitHub Actions job that builds `hzcommfix.so` from source and checks that every Python tool compiles. |

The game's original assets, the built paks and any game files are never committed (see `.gitignore`).

## How it works

HumanitZ 1.1 built the Community system around a listen-server host. On a dedicated server the native subsystem
`UHZCommunityNPCSubSys` (which stores every community and simulates the NPCs: tasks, hunger, morale, travel) is never
created, and several pieces of data (community list, base name, NPC data with `TSet`/`TMap`) are not replicated.

### Server: native fix ("step 2")

`UHZCommunityNPCSubSys::ShouldCreateSubsystem` refuses dedicated servers. All three tools make it return the result
of the parent `UWorldSubsystem::ShouldCreateSubsystem`, like the host/single-player build does. The function is found
**by byte pattern**, never by a fixed address.

| Tool | Target | Pattern (`??` = any byte) | Offset | New bytes |
|---|---|---|---|---|
| `hzcommfix.so` (LD_PRELOAD, in memory only) / `humanitz_npc_patcher.py` | `HumanitZServer-Linux-Shipping` | `53 48 89 F3 E8 ?? ?? ?? ?? 48 85 DB 74 09 84 C0 74 05 E8 ?? ?? ?? ?? 31 C0 5B C3` | 9 | `5B C3 90` |
| `humanitz_npc_patcher.ps1` / `humanitz_npc_patcher.py` | `HumanitZServer-Win64-Shipping.exe` | `40 53 48 83 EC 20 48 8B DA E8 ?? ?? ?? ?? 84 C0 74 0A 48 85 DB 74 05 E8 ?? ?? ?? ?? 32 C0 48 83 C4 20 5B C3` | 16 | `EB 0C` |

Safety checks:

- The pattern must be found **exactly once**; otherwise nothing is changed (unknown game version).
- `hzcommfix.so` only acts inside the `HumanitZServer-Linux-Shipping` process, reads `/proc/self/maps` to find the
  code and uses `mprotect` to write the 3 bytes in its own memory. It writes nothing to disk, uses no network and
  starts no processes. It prints `[hzcommfix] subsistema de comunidade habilitado no servidor dedicado` to the
  process output (stdout/stderr), not to the game's `HumanitZServer.log`.
- The patchers are plain-text scripts, keep a `.bak` copy of the executable and can restore it (`-Restore` /
  `--restore`, or running the PowerShell script again). They download nothing and use no network. There is no
  `.bat`, `.exe` or `-ExecutionPolicy Bypass` in the package.

### Paks (Blueprint changes)

| Pak | Assets replaced |
|---|---|
| Server | `BP_HMZQuestComp`, `BP_GameStateBase`, `BP_GameModeSave`, `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `C-Building` |
| Client | `BP_HMZQuestComp`, `UI_HMZQuest`, `UI_CommunityTab`, `UI_CommunityMemberInfo`, `UI_PreTaskInfo`, `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `BP_CharacterBase` |

- **Sync** (`build_sync.py`): every 2 s the server sends each player the data of their community (`TSet`/`TMap`
  flattened into arrays and rebuilt on the client). The base name is replicated and sent immediately when renamed.
- **Actions** (`build_rpcs.py`): every management action in the UI goes to the server through one of 11 server RPCs
  (assign/schedule/clear task, follow, follow NPC, sleep, hold position, friendly, equip, sync NPC); the server
  validates and applies it.
- **Client subsystem** (`build_commsub.py`, `swap_subsys.py`): the client executable is never modified. On a client
  connected to a dedicated server the mod creates its own instance of the subsystem only to hold the synced data (no
  local simulation). In single-player or when hosting, the original behaviour is kept.
- **Server spawning and building** (`patch_gs.py`, `patch_cbuild.py`, `patch_dismantle.py`, `patch_basename.py`,
  `flipnet.py`): recruitable NPCs are spawned on the dedicated server, the base can be built and dismantled without a
  host, and the base name is replicated.
- **Save protection** (`patch_savecomm.py`, 1.0.2): the save only writes community data when the subsystem exists.
- **Orphan base repair and message** (`build_sync.py --server`, `patch_showmsg.py`, 1.0.2): uses the game's own native
  functions (`GetCommunityLevel`, `AddNewCommunity`, `UpgradeBase`). Only the player who built the base (its GUID is in
  that player's community list) gets it repaired; bases in nobody's list are not touched. The message uses the existing
  `CLIENT_ShowQuestMessage` RPC and the game's tutorial pop-up, translated to the game's 10 languages.

## Building

### Requirements

- Python 3.10+ (standard library only), bash, zip
- gcc and binutils (`strip`) for `hzcommfix.so`
- A HumanitZ installation (client and dedicated server) to extract the original assets from

### 1. Extract the original assets

The game's assets are not distributed. Extract each one from the game's own `.pak` into `originals/`, as a single
`.bin` file (`.uasset` and `.uexp` concatenated):

```sh
# lists the full /Game/... paths of the assets
python3 tools/zpaths.py <game .pak> BP_HMZQuestComp BP_GameModeSave
# extracts every asset that contains one of the terms into <outdir>/<offset>.bin
python3 tools/zfindall2.py <game .pak> <outdir> BP_HMZQuestComp_C
```

Rename the extracted files to the names `build.sh` expects. Files ending in `_srv` come from the dedicated server
(`HumanitZServer`), files ending in `_cli` come from the game client (`HumanitZ`):

```
quest_srv.bin  quest_cli.bin  BPK_CommunityBaseLevel1_srv.bin  BPK_CommunityBaseLevel1_cli.bin
BP_BaseInteractActor_srv.bin  BP_BaseInteractActor_cli.bin  BP_CharacterBase_cli.bin  BP_GameStateBase_srv.bin
BP_GameModeSave_srv.bin  C-Building_srv.bin  UI_HMZQuest_cli.bin  UI_CommunityTab_cli.bin
UI_CommunityMemberInfo_cli.bin  UI_PreTaskInfo_cli.bin
```

(`quest_*.bin` is `BP_HMZQuestComp`.)

### 2. Build the paks

```sh
bash build.sh
# -> paks/zz_CommunityFix_P.pak (server) and paks/HumanitZ_CommunityFix_P.pak (client)
```

The build is reproducible: the same original assets produce the same bytes. Optionally, create `build.local.sh`
(not versioned) with `HZ_SERVER_BIN=<server executable>` and `HZ_CLIENT_EXE=<client executable>`, and `build.sh` will
also check with `tools/check_imports.py` that every native function the edited assets call exists in that game build.

### 3. Build `hzcommfix.so`

```sh
gcc -O2 -shared -fPIC -o shim/hzcommfix.so shim/hzcommfix.c
strip --strip-unneeded shim/hzcommfix.so
```

The released binary (unchanged since 1.0.1) was built on Ubuntu 22.04 with GCC 11.4 (recorded in its `.comment`
section). Rebuilding with GCC 11 gives the same 213 instructions (apart from addresses) and a byte-identical `.rodata`
section. To compare a fresh build with the released file:

```sh
REL=HumanitZServer/Binaries/Linux/hzcommfix.so   # from the release zip
NEW=shim/hzcommfix.so
dis() { objdump -d --no-show-raw-insn "$1" | sed -n '/<.text>:/,$p' | grep -P '^\s+[0-9a-f]+:\t' \
        | cut -f2- | sed -E 's/[0-9a-f]+ <[^>]*>/ADDR/g; s/-?0x[0-9a-f]+\(%rip\)/RIP/g'; }
diff <(dis "$REL") <(dis "$NEW") && echo "same instructions"
cmp <(objcopy -O binary --only-section=.rodata "$REL" /dev/stdout) \
    <(objcopy -O binary --only-section=.rodata "$NEW" /dev/stdout) && echo "same constant data"
```

### 4. Pack the release

```sh
bash release.sh 1.0.2
# -> release/dist/NPCCommunityFix_Client_v1.0.2.zip and release/dist/NPCCommunityFix_DedicatedServer_v1.0.2.zip
```

Compare the result with `SHA256SUMS.txt`.

## Installing

Server owners extract the server zip into the server root (the folder that contains `HumanitZServer`) and enable
step 2 for their OS. Players install the client zip with Vortex or copy the pak to `HumanitZ\Content\Paks\~mods`.
Step-by-step instructions (English + Portuguese) are in `release/servidor/LEIA-ME_README.txt`,
`release/cliente/LEIA-ME_README.txt` and on the Nexus Mods page.

## Changelog

### 1.0.2 (2026-10-28)

- Save protection: without step 2, community data stays in the save instead of being erased.
- Automatic repair of Community Bases built or upgraded while step 2 was inactive (owner online, step 2 active). The
  community is recreated at the base level and named "(Rename your community)". Survivors from a lost community do not
  come back.
- "Community restored" pop-up for the owner, in the game's language (10 languages, AI-translated). Clients on 1.0.1 or
  older see it in English as a small quest message.
- The "Replicated TMaps are not supported" server log error no longer repeats every 2 seconds.
- Server README: new section on keeping step 2 active.
- Build: new `tools/patch_savecomm.py`, `tools/patch_showmsg.py`, `tools/check_imports.py` (native import check in
  `build.sh`) and `tools/minidump.py` (crash dump reader for diagnosis).
- Client and server paks changed; the Linux library and the patchers are unchanged from 1.0.1.
- Tested with Steam client build 26148751 and dedicated server builds 26172841 (Linux) / 26172878 (Windows),
  on a local Linux server and on AMP (CubeCoders).

### 1.0.1 (2026-10-23)

- Updated for the game hotfix of 2026-10-23 (HumanitZ 1.1B), keeping the hotfix changes in the replaced assets.
- Server package is a single zip extracted into the server root; the Windows patcher is a plain-text PowerShell
  script (no `.bat` or `.exe`).
- Builders no longer rely on absolute offsets.

### 1.0.0 (2026-10-21)

- First release: NPC recruitment and Community management on dedicated servers; client only needs a pak; Linux
  server fix via LD_PRELOAD (no file changes); Windows server patcher.

## Credits and AI disclosure

Made by **lionademais**. The mod was developed with the help of AI (Claude) for reverse engineering, the asset-editing
tools, the server fix, the translations and the documentation, and tested by the author on real setups.
