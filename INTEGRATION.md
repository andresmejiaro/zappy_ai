# Zappy Integration Notes

Repo mapping in this workspace:

- `.` = AI client repo (`zappy_ai`)
- `external/zappy` = game server repo
- `external/ZAPPY_GC` = graphic GUI client repo

## 1. Detected Language / Build System

| Repo | Role | Language(s) | Build / packaging system | Evidence |
| --- | --- | --- | --- | --- |
| `.` | AI client | Python 3 | `setuptools` via `pyproject.toml`; helper `Makefile` | `pyproject.toml`, `src/zappy_ai/*.py`, root `Makefile` |
| `external/zappy` | Server | C++17 | GNU Make + `c++` | `external/zappy/Makefile`, `-std=c++17`, `srcs/*.cpp` |
| `external/ZAPPY_GC` | GUI / graphic client | Godot 4 GDScript | Godot CLI wrapped by GNU Make | `project.godot`, `Scripts/*.gd`, `external/ZAPPY_GC/Makefile` |

Notes:

- The GUI repo has a `[dotnet]` assembly name in `project.godot`, but this checkout contains GDScript files only and no `.cs`, `.csproj`, or solution files.
- The server README says "written in C++17", and the build matches that.

## 2. How Each Component Is Currently Started

### AI (`.`)

Primary run path:

```bash
python -m zappy_ai.client -p <port> -n <team> [-h <host>]
```

Current repo-provided helpers:

- `README.md` recommends `pip install -e .` and then `python -m zappy_ai.client`
- Root `Makefile` can:
  - build a zipapp launcher named `client`
  - run many clients with `make run-clients`

Relevant current defaults from the root `Makefile`:

- `HOST=127.0.0.1`
- `PORT=4444`
- `N=13`
- `NAME=pollo`
- `VENV=$(HOME)/py312`

### Server (`external/zappy`)

Build:

```bash
make -C external/zappy
```

Run:

```bash
./external/zappy/server -p <port> -x <width> -y <height> -n <team...> -c <nb_clients> -t <tick_freq> [-d]
```

There is already a compiled `external/zappy/server` binary present in this workspace.

### GUI (`external/ZAPPY_GC`)

Run in-editor / from Godot:

```bash
make -C external/ZAPPY_GC run
```

Equivalent direct form:

```bash
godot4 --path external/ZAPPY_GC
```

Current startup behavior:

- `project.godot` boots `res://Scenes/MainMenuUI.tscn`
- `Scripts/StartButton.gd` auto-presses itself on `_ready()`
- that immediately emits a connection request using defaults `127.0.0.1:4242` unless the menu fields override them first

Export path currently intended by the repo:

```bash
make -C external/ZAPPY_GC
```

That tries to export a Linux build to `external/ZAPPY_GC/build/gfx`.

## 3. Required Ports, CLI Args, Env Vars, Assets, Config Files

### AI (`.`)

Ports / host:

- Connects to the server TCP port supplied by `-p`
- Host defaults to `localhost` in `src/zappy_ai/client.py`

CLI args:

- `-p <port>` required
- `-n <team>` required
- `-h <host>` optional

Env vars:

- None used by the Python code

Dependencies:

- `numpy` is imported at runtime
- `pyproject.toml` does not declare `numpy`; the root `Makefile` installs it manually

Config / files:

- `pyproject.toml`
- source package under `src/zappy_ai`
- optional local venv, but the checked-in `Makefile` assumes `$(HOME)/py312`, not `./.venv`

### Server (`external/zappy`)

Ports / bind:

- `-p <port>` required
- binds `INADDR_ANY` on that port

CLI args:

- `-p <port>` required
- `-x <width>` required
- `-y <height>` required
- `-n <team1> [team2 ...]` required
- `-c <nb_clients>` required
- `-t <tick_freq>` required
- `-d` optional debug flag

Accepted ranges enforced by the parser:

- port: `0..65535`
- width / height: `1..1024`
- time frequency: `1..1000`
- client slots: `>= 1`

Env vars:

- None used by the server code

Assets / config:

- no external asset pack or config file is required at runtime
- build is driven by `Makefile`

### GUI (`external/ZAPPY_GC`)

Ports / host:

- connects to the host and port entered in the menu
- current defaults in `Scripts/StartButton.gd` are:
  - host `127.0.0.1`
  - port `4242`

CLI args:

- none defined by the project itself
- the run path depends on Godot CLI, e.g. `godot4 --path external/ZAPPY_GC`

Env vars:

- none used by the Godot scripts

Required project files / assets:

- `project.godot`
- `Scenes/`
- `Prefabs/`
- `Scripts/`
- `Assets/` including models, textures, music, and audio

Autoloaded singletons from `project.godot`:

- `SignalBus`
- `SceneManager`
- `Network`
- `Crt`

Protocol reference file:

- `external/ZAPPY_GC/commands.txt`

## 4. Protocol Assumptions Between Server / AI / GUI

There is no direct AI-to-GUI channel. Both are separate TCP clients of the server.

### Server <-> AI

Handshake assumed by the AI:

1. server sends `BIENVENUE`
2. AI sends the team name as a bare line
3. server replies with:
   - available client slots as an integer line
   - map size as `<width> <height>`

This matches the current server handshake implementation.

After handshake, the AI assumes the player protocol is line-based and case-sensitive. Commands it sends are lowercase:

- `avance`
- `droite`
- `gauche`
- `voir`
- `inventaire`
- `prend <item>`
- `pose <item>`
- `broadcast <json>`
- `fork`
- `incantation`
- `connect_nbr`

Responses the AI explicitly parses:

- `ok`
- `ko`
- `{...}` map / inventory payloads
- integer-only lines
- `niveau actuel : <n>`
- `message <direction>,<payload>`
- `mort`

### Server <-> GUI

Handshake assumed by the GUI:

- as soon as TCP reaches `STATUS_CONNECTED`, the GUI sends `GRAPHIC\n`
- it does not wait for `BIENVENUE`
- it expects the server to begin streaming the full graphic state after that

This matches the server's `GRAPHIC` handshake path:

- the server marks the socket as a graphic client
- then sends a startup snapshot built by `welcome_graphic()`

Current server startup snapshot for a graphic client:

- `msz`
- `sgt`
- full map content as repeated `bct`
- `tna` for each team
- `pnw` for connected players
- `enw` for disconnected-but-hatched eggs

Graphic/event commands the GUI currently parses or reacts to:

- `msz`
- `tna`
- `bct`
- `pnw`
- `pin`
- `ppo`
- `plv`
- `pgt`
- `pbc`
- `pdi`
- `pic`
- `pie`
- `pfk`
- `enw`
- `eht`
- `ebo`
- `edi`
- `sgt`
- `sst`
- `seg`
- `smg`

Commands the GUI currently only logs / ignores:

- `pex`
- `pdr`
- `suc`
- `sbp`
- `BIENVENUE`

### Shared assumptions / integration quirks

- The reserved team name `GRAPHIC` cannot be used as a normal team name.
- The AI and GUI currently disagree on their default server port:
  - AI `Makefile`: `4444`
  - GUI menu/default auto-connect: `4242`
- The GUI is passive after `GRAPHIC`; it does not actively request `msz` / `mct` / `tna`.
- The server command parser is case-sensitive. The current AI lowercase commands and GUI uppercase `GRAPHIC` handshake both match the implementation.

## 5. Missing Dependencies or Unknowns

Concrete integration gaps found in the current checkout:

- `numpy` is a required AI runtime dependency but is not declared in `pyproject.toml`.
- Root `README.md` says `python`, but `python` is not guaranteed to exist on PATH here; this workspace does have `./.venv/bin/python`.
- The root `Makefile` assumes `$(HOME)/py312`, while the workspace already contains `./.venv`.
- AI default port (`4444`) and GUI default port (`4242`) are inconsistent.
- The GUI export path looks incomplete:
  - `external/ZAPPY_GC/Makefile` expects an export preset `"Linux/X11"`
  - no `export_presets.cfg` was found
  - `external/ZAPPY_GC/build/` exists but is empty
  - `external/ZAPPY_GC/export_templates/` exists but is empty
- The GUI therefore looks runnable from Godot, but not obviously exportable from this checkout without extra setup.
- The server build enables `-fsanitize=address` by default, so the runtime environment needs a compatible compiler / ASan runtime.
- No top-level shared config establishes a canonical port, team name, or boot sequence across all three repos.

Useful but non-blocking note:

- `external/ZAPPY_GC/TestServer/script.py` is a protocol playback test harness for the GUI, but it does not emulate the real server greeting exactly; it is not a drop-in substitute for AI testing.

## 6. Smallest Possible Local Demo Command Sequence

Assumptions:

- use the existing checked-in `external/zappy/server` binary
- use the existing `./.venv`
- `godot4` or `godot` is installed and on PATH

Recommended minimal sequence in three terminals:

Terminal 1:

```bash
./external/zappy/server -p 4242 -x 10 -y 10 -n pollo -c 4 -t 100
```

Terminal 2:

```bash
make -C external/ZAPPY_GC run
```

Terminal 3:

```bash
./.venv/bin/pip install numpy
./.venv/bin/pip install -e .
./.venv/bin/python -m zappy_ai.client -h 127.0.0.1 -p 4242 -n pollo
```

If the server binary is missing or stale, prepend:

```bash
make -C external/zappy
```

If you want to use the AI repo's `make run-clients`, you must override its default port so it matches the GUI/server choice, for example:

```bash
make PORT=4242 NAME=pollo run-clients
```
