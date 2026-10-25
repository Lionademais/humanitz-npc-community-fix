# NPC Mechanics on Dedicated Server (HumanitZ)

Source code and build instructions for the native/script parts of the HumanitZ mod
**NPC Mechanics on Dedicated Server** (internal name *NPC Community Dedicated Fix*).

- Nexus Mods page: https://www.nexusmods.com/games/humanitz/mods/171
- Current release: **1.0.1**, for **HumanitZ 1.1B** (release 1.0.0 was made for HumanitZ 1.1A)

HumanitZ 1.1 added recruitable NPCs and Communities, but on dedicated servers the feature does not work: the
game's native NPC community subsystem (`UHZCommunityNPCSubSys`) is never created on the dedicated server build.
This mod makes the Community system work on dedicated servers, with the server as the single source of truth.

## What is in this repository

| Path | What it is | Shipped in the Nexus file as |
|---|---|---|
| `server/linux/hzcommfix.c` | Linux library loaded with `LD_PRELOAD`. Enables the subsystem **in memory only** (3 bytes) at server startup. | `HumanitZServer/Binaries/Linux/hzcommfix.so` (compiled) and `extras/hzcommfix.c` |
| `server/linux/Makefile` | Build script for `hzcommfix.so`. | - |
| `server/windows/humanitz_npc_patcher.ps1` | Plain-text PowerShell script for Windows dedicated servers. Patches 2 bytes of the server executable. | `HumanitZServer/Binaries/Win64/humanitz_npc_patcher.ps1` |
| `server/tools/humanitz_npc_patcher.py` | Plain-text Python alternative (Windows or Linux server executable). | `extras/humanitz_npc_patcher.py` |
| `docs/` | The README files shipped inside the Nexus zips (English + Portuguese). | `LEIA-ME_README.txt` |
| `SHA256SUMS.txt` | SHA-256 of every file in the 1.0.1 release zips. | - |
| `.github/workflows/build.yml` | GitHub Actions job that builds `hzcommfix.so` from source on Ubuntu 22.04. | - |

`hzcommfix.so` is the **only compiled binary** in the mod. The scripts are plain text and run as-is. The mod
contains no `.exe`, `.dll` or `.bat` files, downloads nothing from the internet and only touches the HumanitZ
dedicated server files.

## What the code changes

All three tools make the same change: inside `UHZCommunityNPCSubSys::ShouldCreateSubsystem`, the dedicated
server build always returns `false`. The tools find that function **by byte pattern** (never by fixed address)
and change it to return the result of the parent `UWorldSubsystem::ShouldCreateSubsystem`, like the
host/single-player build does.

| Target | Byte pattern (`??` = any byte) | Offset | New bytes |
|---|---|---|---|
| Linux server (`HumanitZServer-Linux-Shipping`) | `53 48 89 F3 E8 ?? ?? ?? ?? 48 85 DB 74 09 84 C0 74 05 E8 ?? ?? ?? ?? 31 C0 5B C3` | 9 | `5B C3 90` (`pop rbx; ret; nop`) |
| Windows server (`HumanitZServer-Win64-Shipping.exe`) | `40 53 48 83 EC 20 48 8B DA E8 ?? ?? ?? ?? 84 C0 74 0A 48 85 DB 74 05 E8 ?? ?? ?? ?? 32 C0 48 83 C4 20 5B C3` | 16 | `EB 0C` (`jmp` over the `return false`) |

Safety checks in every tool:

- The pattern must be found **exactly once**; otherwise nothing is changed (unknown game version).
- `hzcommfix.so` only acts inside the `HumanitZServer-Linux-Shipping` process (`LD_PRELOAD` also reaches the
  startup shell script) and never writes to disk.
- The patchers keep a `.bak` copy of the executable and can restore it (`-Restore` / `--restore`, or running the
  PowerShell script again when the patch is already applied).

## Building `hzcommfix.so`

Requirements: Linux x86-64, `gcc`, `make`, `binutils` (`strip`).

```sh
make -C server/linux
# equivalent to:
gcc -O2 -shared -fPIC -o hzcommfix.so server/linux/hzcommfix.c
strip --strip-unneeded hzcommfix.so
```

The 1.0.1 release binary was built on **Ubuntu 22.04 with GCC 11.4** (recorded in its `.comment` section:
`GCC: (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`). To build in the same environment:

```sh
docker run --rm -v "$PWD:/src" -w /src ubuntu:22.04 \
  bash -c "apt-get update && apt-get install -y gcc make binutils && make -C server/linux"
```

The GitHub Actions workflow in this repository does the same on an `ubuntu-22.04` runner and publishes the
result as a build artifact.

### Checking the released binary against this source

Byte-for-byte identical builds depend on the exact compiler, glibc and linker versions, so the hash of a fresh
build can differ from the released file. To compare the code itself:

```sh
# released file from the Nexus zip
REL=HumanitZServer/Binaries/Linux/hzcommfix.so
make -C server/linux
NEW=server/linux/hzcommfix.so

# code: same instructions (addresses and RIP-relative offsets removed)
dis() { objdump -d --no-show-raw-insn "$1" | sed -n '/<.text>:/,$p' | grep -P '^\s+[0-9a-f]+:\t' \
        | cut -f2- | sed -E 's/[0-9a-f]+ <[^>]*>/ADDR/g; s/-?0x[0-9a-f]+\(%rip\)/RIP/g'; }
diff <(dis "$REL") <(dis "$NEW") && echo "same instructions"

# constant data (byte pattern, messages): identical
cmp <(objcopy -O binary --only-section=.rodata "$REL" /dev/stdout) \
    <(objcopy -O binary --only-section=.rodata "$NEW" /dev/stdout)

# imported functions
nm -D "$REL"; nm -D "$NEW"
```

Building with GCC 11 gives the same `.text` size (873 bytes), the same 213 instructions apart from addresses and a
byte-identical `.rodata` section. The library imports only standard libc functions: `readlink`, `fopen`, `fgets`,
`sscanf`, `fclose`, `strstr`, `strcmp`, `sysconf`, `mprotect`, `fputs`, `fflush`, `snprintf`.

## Using the scripts

No build step: they are run directly.

```powershell
# Windows dedicated server (built into Windows, nothing to install)
# Right-click humanitz_npc_patcher.ps1 -> "Run with PowerShell", or:
powershell -File humanitz_npc_patcher.ps1 [-Exe path\to\HumanitZServer-Win64-Shipping.exe] [-Restore] [-NoPause]
```

```sh
# Python alternative (Windows or Linux server executable)
python3 humanitz_npc_patcher.py <server executable>
python3 humanitz_npc_patcher.py --restore <server executable>
```

Full installation steps for server owners and players are in `docs/` and on the Nexus Mods page.

## The `.pak` files

The client pak (`NPCCommunityFix_Client_P.pak`) and the server pak (`NPCCommunityFix_Server_P.pak`) contain only
Unreal Engine 4.27 assets (`.uasset` / `.uexp`, Blueprints and UI widgets) edited from the game's own assets. They
contain no native code. Because they are derived from the game's copyrighted content, they are not committed to
this repository; they are distributed only through the Nexus Mods page.

| Pak | Assets replaced |
|---|---|
| Client | `BP_HMZQuestComp`, `UI_HMZQuest`, `UI_CommunityTab`, `UI_CommunityMemberInfo`, `UI_PreTaskInfo`, `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `BP_CharacterBase` |
| Server | `BP_HMZQuestComp`, `BP_GameStateBase`, `BP_BaseInteractActor`, `BPK_CommunityBaseLevel1`, `C-Building` |

What the edited Blueprints do:

- **Sync:** `BP_HMZQuestComp` replicates the community list, player UID and a copy of the community data to each
  player every 2 seconds (`TSet`/`TMap` data is flattened into replicated arrays and rebuilt on the client). The
  base name is replicated and sent immediately when renamed.
- **Actions:** 11 server RPCs (`SRV_*`) repeat on the server the management actions taken in the UI (tasks, follow,
  hold, equip, etc.); the server validates and applies them.
- **Server spawning:** `BP_GameStateBase.HandleNPCRecruits` spawns the recruitable NPCs on the dedicated server, and
  `BP_BaseInteractActor` / `BPK_CommunityBaseLevel1` / `C-Building` allow building and dismantling the Community
  Base without a host.
- **Client:** the game executable is never modified on the client. When connected to a dedicated server the client
  keeps a local copy of the synced data for the UI only (no local simulation). In single-player or when hosting,
  the original behaviour is kept.

## Credits and AI disclosure

Made by **lionademais**. The mod was developed with the help of AI tools (reverse engineering, asset-editing tools,
the server fix and documentation), and tested on a Windows Steam client with Linux dedicated servers (local test
and AMP).
