# NPC Mechanics on Dedicated Server (HumanitZ)

Full source code and build instructions for the HumanitZ mod **NPC Mechanics on Dedicated Server**
(internal name *NPC Community Dedicated Fix*). It makes the NPC recruitment and Community system of HumanitZ 1.1
work on dedicated servers, with the server as the single source of truth.

- **Current release: [1.0.3](https://github.com/Lionademais/humanitz-npc-community-fix/releases/tag/v1.0.3)**, for HumanitZ 1.1B
- Nexus Mods page: https://www.nexusmods.com/games/humanitz/mods/171
- Client and server must always run the **same mod version** (1.0.3 client requires 1.0.3 server and vice versa).

## What's new in 1.0.3

Everything in this version is about the client's Community tab. Recruiting, sync, the orphan base repair, the save
protection and the "Community restored" message work exactly as in 1.0.2.

- **NPC action history translated:** the "Action History" lines in the member sheet were always in English on dedicated
  servers. The client now shows them in the player's game language. NPC lines (333 lines from the game's
  `DT_NPC_Responses`) and task names (`DT_TaskConfig`) use the game's **official translations**; a few fixed phrases
  that the game never translates use the mod's own translations. The server still stores English (the save does not
  change), so players with different languages on the same server each see their own.
- **Community tab labels translated:** several labels are stored in the original game as non-translatable text (English
  in every language, even in single-player). The mod translates them on the client: tab titles, member sheet, task
  details window and the "Morale" label in the member list. The NPC schedule times now use the game's official
  translations.
- **Text fits the panel:** where space is tight, a translation wider than the English text is scaled down to fit
  (measured in game with the real font).
- **Language changes apply in game** within about 2 seconds, including back to English.
- **Fixed the negative trait flickering** in the member sheet every 2 seconds (the game rebuilt the trait list on every
  update).
- Both paks changed: the shared sync component got new internal (non-replicated) properties, so client and server must
  both be on 1.0.3.

Languages: the 10 official HumanitZ languages (English, Portuguese, German, Spanish, French, Italian, Japanese, Korean,
Russian, Chinese). The mod's own translations were made with AI and have not been reviewed by native speakers;
corrections are welcome.

Full history in the [Changelog](#changelog).

## Repository layout

| Path | What it is |
|---|---|
| `build.sh` | Rebuilds both paks from the game's original assets (`originals/`, not included). |
| `release.sh` | Packs the paks, the Linux library and the scripts into the two release zips. |
| `shim/hzcommfix.c` | Source of `hzcommfix.so`, the Linux server library (the only compiled binary in the mod). |
| `tools/` | Python tools (no external dependencies) that read and rebuild cooked UE 4.27 packages, assemble Kismet bytecode, read the game's localization files and write the paks. |
| `tools/ui_translations.py`, `tools/chat_translations.py` | The mod's own translations (Community tab labels and fixed action history phrases). |
| `release/servidor/` | Files shipped in the server zip besides the pak and the library: `LEIA-ME_README.txt`, the Windows patcher (`HumanitZServer/Binaries/Win64/humanitz_npc_patcher.ps1`) and the Python patcher (`extras/humanitz_npc_patcher.py`). |
| `release/cliente/` | `LEIA-ME_README.txt` shipped in the client zip. |
| `SHA256SUMS.txt` | SHA-256 of the release zips and of every file inside them. |
| `.github/workflows/build.yml` | GitHub Actions job that builds `hzcommfix.so` from source and checks that every Python tool compiles. |

The game's original assets and texts, the built paks and any game files are never committed (see `.gitignore`).

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
- Windows check: with game build 26172878, `Get-FileHash HumanitZServer-Win64-Shipping.exe -Algorithm SHA1` gives
  `4920AA5FAEB37ACDBF21E3949BCB665AE7F37B86` for the original executable and `5FB8D76C9E34489D5A59548BD9C892536C009A02`
  with step 2 applied (`74 0A` -> `EB 0C` at offset `0xE62C90`). Running the patcher again is safe: it answers
  "already applied" or applies the patch.

### Paks (Blueprint changes)

| Pak | Assets replaced |
|---|---|
| Server | `BP_HMZQuestComp`, `BP_GameStateBase`, `BP_GameModeSave`, `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `C-Building` |
| Client | `BP_HMZQuestComp`, `UI_HMZQuest`, `UI_CommunityTab`, `UI_CommunityMemberInfo`, `UI_PreTaskInfo`, `UI_CommunityMember` (1.0.3), `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `BP_CharacterBase` |

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
- **Action history translation** (`build_sync.py`, `chat_translations.py`, 1.0.3): the client translates its replicated
  copy of the community data before handing it to its local subsystem, using `FindTextInLocalizationTable` with the
  official key of each line (empty namespace of `Game.locres`), and keeps "translated line -> English original" to
  translate again when the language changes. The translation table is generated at build time from
  `DT_NPC_Responses`, `DT_TaskConfig` and the lines written by the NPC Blueprints. New non-replicated properties exist
  on both sides, which is why the server pak changed too.
- **Community tab labels** (`patch_uitexts.py`, `ui_translations.py`, 1.0.3): `SetText` on the widgets' text blocks for
  the culture from `GetCurrentCulture`; schedule times use the game's own localized text. Each widget compares the
  language on every update and only reapplies when it changed. Fit: the English text and the translation are measured
  in the same text block (`ForceLayoutPrepass` + `GetDesiredSize`) and `SetRenderScale` shrinks the translation when it
  is wider than the allowed limit.
- **Trait list** (`patch_traitui.py`, 1.0.3): the member sheet keeps a signature (member, revealed traits, trait counts)
  and skips rebuilding the trait list when it did not change.

## Building

### Requirements

- Python 3.10+ (standard library only), bash, zip
- gcc and binutils (`strip`) for `hzcommfix.so`
- A HumanitZ installation (client and dedicated server) to extract the original assets and texts from

### 1. Extract the original assets and texts

The game's assets and texts are not distributed. Extract each asset from the game's own `.pak` into `originals/`, as a
single `.bin` file (`.uasset` and `.uexp` concatenated):

```sh
# lists the full /Game/... paths of the assets
python3 tools/zpaths.py <game .pak> BP_HMZQuestComp UI_CommunityMember
# extracts every asset that contains one of the terms into <outdir>/<offset>.bin
python3 tools/zfindall2.py <game .pak> <outdir> BP_HMZQuestComp_C
# extracts every .locres file from the pak into <outdir>/<offset>.locres
python3 tools/zlocres.py <game .pak> <outdir>
```

Some data tables are stored without compression in the pak and do not show up in the zlib searches; use
`tools/zextract.py` with their offsets. Rename the extracted files to the names the build expects. Files ending in
`_srv` come from the dedicated server (`HumanitZServer`), files ending in `_cli` from the game client (`HumanitZ`):

```
originals/
  quest_srv.bin  quest_cli.bin                      (BP_HMZQuestComp)
  BPK_CommunityBaseLevel1_srv.bin  BPK_CommunityBaseLevel1_cli.bin
  BP_BaseInteractActor_srv.bin  BP_BaseInteractActor_cli.bin
  BP_CharacterBase_cli.bin  BP_GameStateBase_srv.bin  BP_GameModeSave_srv.bin  C-Building_srv.bin
  UI_HMZQuest_cli.bin  UI_CommunityTab_cli.bin  UI_CommunityMemberInfo_cli.bin  UI_PreTaskInfo_cli.bin
  UI_CommunityMember_cli.bin
  DT_NPC_Responses_srv.bin  DT_TaskConfig_srv.bin   (action history translation)
  historico/BP_Recruit_NPC_srv.bin  historico/BT_NPC_CheckVitals_srv.bin  historico/BT_NPC_HandleTasks_srv.bin
  locres/Game_<culture>.locres                      (the 10 languages, e.g. Game_en.locres, Game_pt.locres)
```

### 2. Build the paks

```sh
bash build.sh
# -> paks/zz_CommunityFix_P.pak (server) and paks/HumanitZ_CommunityFix_P.pak (client)
```

The build is reproducible: the same original assets produce the same bytes (checked with two builds). Optionally,
create `build.local.sh` (not versioned) with `HZ_SERVER_BIN=<server executable>` and `HZ_CLIENT_EXE=<client executable>`,
and `build.sh` will also check with `tools/check_imports.py` that every native function the edited assets call exists
in that game build. `tools/ufunc_sig.py` reads the registered parameters of a native function from the executable.

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
bash release.sh 1.0.3              # test build   -> teste/
bash release.sh 1.0.3 --publicar   # release      -> versoes/
# NPCCommunityFix_Client_v1.0.3.zip and NPCCommunityFix_DedicatedServer_v1.0.3.zip
```

Compare the result with `SHA256SUMS.txt`.

## Installing

Server owners extract the server zip into the server root (the folder that contains `HumanitZServer`) and enable
step 2 for their OS. Players install the client zip with Vortex or copy the pak to `HumanitZ\Content\Paks\~mods`
(only one copy). Step-by-step instructions (English + Portuguese) are in `release/servidor/LEIA-ME_README.txt`,
`release/cliente/LEIA-ME_README.txt` and on the Nexus Mods page.

## Changelog

### 1.0.3 (2026-10-29)

- NPC action history ("Action History") shown in the player's game language: official game translations for NPC lines
  and task names, the mod's own translations for the fixed phrases the game never translates ("{name} has died.",
  "Taking a short break.", "I can't deal with {name} anymore, I'm leaving the camp!", "Task failed", "Task <line>").
  Unknown lines stay in English.
- Community tab labels that the game stores as non-translatable text are translated on the client (tab, member sheet,
  task details window, "Morale" in the member list); schedule times use the game's official translations.
- Translations that do not fit are scaled down; the big notice and "Supply" wrap to two lines if needed.
- Changing the game language in game updates the labels and the history within about 2 seconds.
- Fixed the negative trait (and what is below it) flickering every 2 seconds in the member sheet.
- `UI_CommunityMember` added to the client pak. Both paks changed (new non-replicated properties in the shared sync
  component), so client and server must both be on 1.0.3.
- Build: new `tools/patch_uitexts.py`, `tools/ui_translations.py`, `tools/patch_traitui.py`,
  `tools/chat_translations.py`, `tools/locres.py`, `tools/zlocres.py`, `tools/ufunc_sig.py`, `tools/uitree.py`,
  `tools/uitags.py`; `release.sh` writes to `teste/` or, with `--publicar`, to `versoes/`.
- The Linux library, the patchers and the README files are unchanged from 1.0.2.
- Tested with Steam client build 26148751 and dedicated server build 26172841 (Linux, local test server), including
  Portuguese in game and changing the language in game. Windows server build 26172878: native part unchanged.

### 1.0.2 (2026-10-28)

- Save protection: without step 2, community data stays in the save instead of being erased.
- Automatic repair of Community Bases built or upgraded while step 2 was inactive (owner online, step 2 active). The
  community is recreated at the base level and named "(Rename your community)". Survivors from a lost community do not
  come back.
- "Community restored" pop-up for the owner, in the game's language (10 languages, AI-translated). Clients on 1.0.1 or
  older see it in English as a small quest message.
- The "Replicated TMaps are not supported" server log error no longer repeats every 2 seconds.
- Server README: new section on keeping step 2 active.
- Build: new `tools/patch_savecomm.py`, `tools/patch_showmsg.py`, `tools/check_imports.py` and `tools/minidump.py`.

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
