# NPC Mechanics on Dedicated Server (HumanitZ)

Source code, build instructions and downloads for the HumanitZ mod **NPC Mechanics on Dedicated Server**
(formerly *NPC Community Dedicated Fix*). It makes the game's own NPC recruitment and Community system work on
dedicated servers, with the server as the single source of truth.

- Nexus Mods page: https://www.nexusmods.com/games/humanitz/mods/171
- **Current release: [client 1.0.8, server Native 1.0.10, server Pak-Only 1.1.2](https://github.com/Lionademais/humanitz-npc-community-fix/releases/tag/v1.1.2)**,
  for the HumanitZ update of 2026-10-30 (HumanitZ 1.1X)

## Downloads: one client, two server options

Players install the **client 1.0.8**. The server owner installs **only one** of the two server options. The client
is the same for both: the server number goes up when only the server changes.

| | Server Pak-Only 1.1.2 | Server Native 1.0.10 |
|---|---|---|
| Where to download | Nexus Mods and this repository | **Only this repository** |
| Files | Three pak files (`.pak/.ucas/.utoc`), one zip for Linux and one for Windows | Pak files plus the native fix: `hzcommfix.so` (Linux), `humanitz_npc_patcher.ps1` (Windows), Python patcher and source in `extras/` |
| Game executable | Not touched: no library, no `LD_PRELOAD`, no patcher | Linux: patched in memory at startup. Windows: 2 bytes patched in the executable |
| Best for | Rented servers whose panel only lets you upload files | Your own machine, VPS or AMP, where you control how the server starts |
| Community simulation | The mod creates the subsystem and runs its own clock with the game's numbers | The game's own native code |
| Behaviour | Fixes several trait bugs of the game; communities keep living when no player is near | Exactly like the game, bugs included |
| World protection | No: back up your saves | Linux: start lock, backup vault and repair (see below) |

### Why the Native option is only on GitHub

The Native option contains a compiled Linux library and scripts that patch the dedicated server executable. Files
like these are held by the automatic security checks of Nexus Mods for a manual review, which has been taking a long
time. To keep the Nexus page clean and its files available, Nexus only hosts files that are plain Unreal Engine paks
(the client and the Pak-Only server). The Native option is distributed here, next to its full source code.

## What's new since 1.0.3

- **New Pak-Only server option (1.1.0 to 1.1.2):** works without touching the game executable, on Linux and Windows.
- **Clan communities (1.0.7):** clan mates share the community. The owner is stored on the base itself and checked
  against the clan list, even offline. Leaving the clan only removes the player from the list.
- **Fixed players being disconnected after many hours on the server (1.0.8):** two internal sync lists grew every
  2 seconds and, above 65,535 entries, the server dropped the player.
- **World protection in `hzcommfix.so` (1.0.4, Native on Linux):** start lock, backup vault and repair.
- **Updated for the HumanitZ update of 2026-10-30** (client 26333407, Linux server 26333826, Windows server 26335264).
  The server paks are back in the IoStore format (`.pak/.ucas/.utoc`) required by the new server build.
- **Extension points for other mods (1.0.9 to 1.0.10 / 1.1.1 to 1.1.2):** actor tags that choose which chests the
  community members use, and chests reserved for one member. Without those tags nothing changes.

Full list in the [Changelog](#changelog).

## Features

- Build, upgrade (levels 1 to 4) and rename the Community Base on a dedicated server.
- Recruit NPCs, including the dialogue options, traits and the "What can you do?" task list.
- Full Community tab: community name, members, member info and supplies.
- Manage members: tasks and schedule, follow, hold position, friendly, sleep, equip and unequip, follower command wheel.
- Members are saved by the server and keep working.
- Clan mates share the community.
- Save protection: without the server fix, community data is not erased from the save.
- Automatic repair of bases left without a community, with a "Community restored" message for the owner.
- Community tab in the player's language (10 languages): official game translations for NPC lines, task names and
  schedule; the mod's own AI-made translations for labels the game never translates.
- Fixed the game's flickering negative trait in the member sheet.

## How it works

HumanitZ 1.1 built the Community system around a listen-server host. On a dedicated server the native subsystem
`UHZCommunityNPCSubSys` (which stores every community and simulates the NPCs: tasks, hunger, morale, travel) is never
created, and several pieces of data (community list, base name, NPC data with `TSet`/`TMap`) are not replicated.

### Client (both options)

One pak; the client executable is never modified. Every 2 seconds the server sends each player the data of their
community (`TSet`/`TMap` flattened into arrays and rebuilt on the client). Each management action in the UI goes to
the server through one of 11 server RPCs; the server validates and applies it. On a client connected to a dedicated
server, the mod creates its own instance of the subsystem only to hold the synced data (no local simulation). In
single-player and hosted games the original behaviour is kept.

### Server Pak-Only

The server pak creates the community subsystem itself (`SpawnObject`) and a new asset, `NPCM_Relogio`, plays the part
of the native `Tick`/`DecayStats` with the game's numbers: hunger, thirst, sleep, cold, dirt, tasks, traits, leaving
the camp and deaths. The clock follows the server's day length (`DayDur`/`NightDur`). Communities keep running in the
data when no player is near: members eat from the base's NPC chests and store task rewards there.

Game bugs fixed only in this option:

- Traits had no value in the save, so no trait rule ever fired. The values now come from the game's own trait table
  (nothing is written to the member's data), and every trait works as the game designed it, including the dangerous
  ones.
- Argumentative, Home_sick, Glutton and Thirsty never triggered; HardWorker finished tasks instantly; Focused protected
  other members by mistake; group traits only updated on load; members who decided to leave the camp stayed.

Known differences: Community tab numbers update every 10 seconds, task notices appear in chat as normal notices, and
saves wait while a member is moving to another base. If the executable is patched or `hzcommfix.so` is loaded, the
clock does not start and the native code is used. Confirmation in `HumanitZServer/Saved/Logs/HumanitZServer.log`:
`LogKaiHelper: NPCM hora=<hour> vel=<speed> dt=<step>` every in-game hour.

### Server Native: the native fix ("step 2")

`UHZCommunityNPCSubSys::ShouldCreateSubsystem` refuses dedicated servers. The tools make it return the result of the
parent `UWorldSubsystem::ShouldCreateSubsystem`, like the host/single-player build does. The function is found **by
byte pattern**, never by a fixed address, and nothing is changed unless the pattern is found exactly once.

| Tool | Target | Pattern (`??` = any byte) | Offset | New bytes |
|---|---|---|---|---|
| `hzcommfix.so` (LD_PRELOAD, in memory) / `humanitz_npc_patcher.py` | `HumanitZServer-Linux-Shipping` | `53 48 89 F3 E8 ?? ?? ?? ?? 48 85 DB 74 09 84 C0 74 05 E8 ?? ?? ?? ?? 31 C0 5B C3` | 9 | `5B C3 90` |
| `humanitz_npc_patcher.ps1` / `humanitz_npc_patcher.py` | `HumanitZServer-Win64-Shipping.exe` | `40 53 48 83 EC 20 48 8B DA E8 ?? ?? ?? ?? 84 C0 74 0A 48 85 DB 74 05 E8 ?? ?? ?? ?? 32 C0 48 83 C4 20 5B C3` | 16 | `EB 0C` |

What `hzcommfix.so` (source: `shim/hzcommfix.c`) does, only inside the `HumanitZServer-Linux-Shipping` process:

- **Fix:** writes the 3 bytes above in the process's own memory (`/proc/self/maps` + `mprotect`). The executable on
  disk is never changed. Prints `[hzcommfix] subsistema de comunidade habilitado no servidor dedicado` to the process
  output (stdout/stderr).
- **Start lock:** if the mod's server pak is missing, is not in IoStore format or was built for another game build
  (checked through its `.sig` file), the server does not start, so the world is never saved without the mod (that
  would make the game roll 40 new recruitable NPCs and break the members' links). `HZ_SEM_TRAVA=1` lets it start anyway.
- **Backup vault:** keeps copies of the recruitable list, the communities and the last healthy world saves in
  `Saved/HZ_Cofre`, rotating old copies.
- **Repair:** if the recruitable list is missing or members lost their link, it restores them from the vault (or by
  the NPC's class), keeping the original save in `Saved/HZ_Cofre/.../antes_reparo_<date>`. If the save format is not
  what it expects, it changes nothing.
- **Log noise:** turns off one game warning that is printed about 120 times per second for members without a task
  (the warning flag of that lookup only; the result is the same).
- It uses no network and starts no processes.

The patchers are plain-text scripts, keep a `.bak` copy of the executable and can restore it. They download nothing
and use no network. There is no `.bat`, `.exe` or `-ExecutionPolicy Bypass`.

Windows check (server build 26335264): `Get-FileHash HumanitZServer-Win64-Shipping.exe -Algorithm SHA1` gives
`807C8B35BF3A122EB7CE87412C5AA57B7508D37F` for the original executable and `45D1548E3F84850B1324FD0B4C1A4CDFFBCB3FA6`
with step 2 (`74 0A` -> `EB 0C` at offset `0xE634B0`).

## Installing

Step-by-step instructions (English + Portuguese) are in the README inside each zip:
`release/cliente/LEIA-ME_README.txt`, `release/servidor/LEIA-ME_README.txt` (Native) and
`release/pakonly/LEIA-ME_README.txt` (Pak-Only).

- **Client:** Vortex, or copy `NPCCommunityFix_Client_P.pak` to `HumanitZ\Content\Paks\~mods` (only one copy).
- **Pak-Only:** stop the server and extract the zip for your OS into the server root (the folder that contains
  `HumanitZServer`), or upload the three `NPCMechanics_PakOnly_Server_P.*` files to `HumanitZServer/Content/Paks`.
  If the Native option was installed, remove it first (its four pak files, the `LD_PRELOAD`, or restore the Windows
  executable).
- **Native:** stop the server, extract the zip into the server root, then enable step 2: `LD_PRELOAD` with the full
  path of `hzcommfix.so` on Linux (AMP: `App.EnvironmentVariables` in `GenericModule.kvp`), or run
  `humanitz_npc_patcher.ps1` on Windows (again after every game update).

## The `.pak` files

The paks contain only Unreal Engine 4.27 assets (Blueprints and UI widgets) edited from the game's own assets, plus
one new asset in the Pak-Only server. They contain no native code. Because they are derived from the game's content,
they are not committed to this repository; they are distributed in the release zips.

| Package | Assets replaced |
|---|---|
| Client 1.0.8 | `BP_HMZQuestComp`, `UI_HMZQuest`, `UI_CommunityTab`, `UI_CommunityMemberInfo`, `UI_PreTaskInfo`, `UI_CommunityMember`, `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `BP_CharacterBase` |
| Server Native 1.0.10 | `BP_HMZQuestComp`, `BP_GameStateBase`, `BP_GameModeSave`, `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `C-Building`, `BP_Recruit_NPC` |
| Server Pak-Only 1.1.2 | The 7 of the Native option + `BP_CharacterBase`, `BP_HmzPlayerController`, `BP_KaiHumanAI_Base`, `BP_NPCHelper`, `BT_NPC_CheckVitals`, `BT_NPC_HandleTasks`, and the new asset `/Game/Mods/NPCMechanics/NPCM_Relogio` |

## Building

### `hzcommfix.so`

```sh
gcc -O2 -shared -fPIC -o shim/hzcommfix.so shim/hzcommfix.c
strip --strip-unneeded shim/hzcommfix.so
```

The released binary was built on Ubuntu 22.04 with GCC 11.4 (recorded in its `.comment` section). The GitHub Actions
workflow builds it from source on an `ubuntu-22.04` runner and publishes the result as an artifact. A rebuild gives a
byte-identical `.rodata` section (byte patterns and messages):

```sh
REL=HumanitZServer/Binaries/Linux/hzcommfix.so   # from the Native zip
cmp <(objcopy -O binary --only-section=.rodata "$REL" /dev/stdout) \
    <(objcopy -O binary --only-section=.rodata shim/hzcommfix.so /dev/stdout) && echo "same constant data"
nm -D "$REL"   # standard libc functions only: files, memory, mprotect, time; no network or process functions
```

### Paks

`build.sh` and the Python tools in `tools/` (standard library only) rebuild the paks from the game's own assets in
`originais/`, which are not distributed; `release.sh` packs the zips. **The pak build tools in this repository are
still those of version 1.0.3**: the tools for the current versions (IoStore format, clan communities, the Pak-Only
server) have not been published here yet. See the 1.0.3 instructions in the
[v1.0.3 README](https://github.com/Lionademais/humanitz-npc-community-fix/blob/v1.0.3/README.md#building).

`SHA256SUMS.txt` lists the SHA-256 of every release zip and of every file inside them.

## Changelog

### Server Native 1.0.10 and Server Pak-Only 1.1.2 (2026-11-05), client stays 1.0.8

- Chest per member (extension point for other mods): a chest tagged `HZXP_<member UID>` only serves that member;
  untagged chests serve everyone. `BP_Recruit_NPC` added to the Native server pak.
- Without tags, the result is identical to the game. Nothing new in the save or on the network.
- Paks inside the zips with 0644 permissions (0600 stopped servers running as another user, such as `amp`, from
  reading them).

### Server Native 1.0.9 and Server Pak-Only 1.1.1 (2026-11-04), client stays 1.0.8

- The chests members use (food, drink, materials, task rewards, clothes, Clepto theft, workbench) come from one
  point of the game, which now honours three actor tags: `HZX_BauNao` removes an NPC chest, `HZX_BauCom` adds any
  chest within 40 m, `HZX_BauPonte` is never used. Without tags, same list and order as the game.

### Server Pak-Only 1.1.0 (2026-11-03): new server option, with client 1.0.8

- The mod creates the community subsystem and runs its own clock with the game's numbers, without touching the
  executable. Separate zips for Linux and Windows.
- Trait bugs fixed (this option only) and communities keep living when no player is near.
- No world protection: back up your saves.

### 1.0.8 (2026-11-03): client and server

- Fixed players being disconnected after many hours (`SyncMTasks`/`SyncMFollow` grew past 65,535 entries).
- Client and server both need 1.0.8 or newer. Built for the HumanitZ update of 2026-10-30.

### 1.0.7 (2026-11-02): server only

- Clan mates share the community. The owner is stored on the base (`ExtraParams`, key `HZCO:<NetID>`) and checked
  against the clan list, even offline.

### 1.0.5 (2026-11-01): server only

- `hzcommfix` v3: silences the game's "task row missing" warning.

### 1.0.4 (2026-10-31)

- Server back to the IoStore format (`.pak/.ucas/.utoc`), required by the new server build.
- `hzcommfix.so` gains the world protection on Linux: start lock (`.sig`), backup vault (`Saved/HZ_Cofre`) and repair.

### 1.0.3 (2026-10-29)

- Community tab translated (NPC action history and labels), text fitted to the panel, language changes in game.
- Fixed the negative trait flickering every 2 seconds.

### 1.0.2 (2026-10-28)

- Save protection, automatic repair of orphan bases with the "Community restored" message, and no more repeated
  "Replicated TMaps are not supported" errors.

### 1.0.1 (2026-10-23)

- Updated for HumanitZ 1.1B; single-zip server package; plain-text Windows patcher (no `.bat` or `.exe`).

### 1.0.0 (2026-10-21)

- First release.

## Credits and AI disclosure

Made by **lionademais**. The mod was developed with the help of AI (Claude) for reverse engineering, the asset-editing
tools, the server fix, the translations and the documentation, and tested by the author on real setups.
