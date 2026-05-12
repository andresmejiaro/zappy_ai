# Zappy AI

Python AI client for Zappy.

This repo is the AI project only. The server and GUI are independent repos used for local integration:

- Server: `https://github.com/PepeSegura/zappy`
- GUI: `https://github.com/Tagamydev/ZAPPY_GC`

The local demo helpers expect those repos under `external/`, but they are not meant to be vendored into this repo permanently.

## Requirements

- Python `>=3.10`; verified locally with Python `3.13.7`
- `numpy`, declared in `pyproject.toml`
- GNU Make
- C++17 toolchain for the server repo
- Godot 4; verified locally with `4.6.1.stable.official.14d19694e`

Create the Python venv from the AI repo root:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -e . --no-build-isolation
```

The demo Makefile targets use `./.venv` through `LOCAL_PY` / `LOCAL_PIP`. The older `client` target still defaults to `$(HOME)/py312`; override `VENV`, `PY`, and `PIP` if you use that path.

## Recreate The Local Integration Layout

From this repo root:

```bash
mkdir -p external
git clone https://github.com/PepeSegura/zappy.git external/zappy
git clone https://github.com/Tagamydev/ZAPPY_GC.git external/ZAPPY_GC
```

Build the server if `external/zappy/server` is not already present:

```bash
make -C external/zappy
```

Expected layout for the local demo:

```text
zappy_ai/
  pyproject.toml
  Makefile
  scripts/
  src/zappy_ai/
  external/zappy/server
  external/ZAPPY_GC/project.godot
```

## Godot Assumptions

The helper script `scripts/find_godot.sh` searches in this order:

1. `GODOT_BIN`, if set
2. `godot4` on `PATH`
3. `godot` on `PATH`
4. `$HOME/Godot/Godot_v4.6.1-stable_linux.x86_64`
5. executable files named `Godot*` under `$HOME/Godot`

If your binary is elsewhere:

```bash
make GODOT_BIN="/path/to/Godot_v4.x-stable_linux.x86_64" demo-preflight
make GODOT_BIN="/path/to/Godot_v4.x-stable_linux.x86_64" demo-full
```

Sanity check without launching the GUI:

```bash
make demo-gui GODOT_ARGS=--version
```

Expected local output:

```text
Using Godot: /home/andres/Godot/Godot_v4.6.1-stable_linux.x86_64
4.6.1.stable.official.14d19694e
```

## GUI Startup Fix

The upstream GUI auto-presses its Play button from `Scripts/StartButton.gd`. `MainScene.tscn` also embeds `MainMenuUI.tscn` inside the pause menu, so without a guard the embedded pause-menu button can auto-connect again after the game scene loads. The symptom is a reconnect loop: the GUI stays near the title/load screen and the server log shows repeated `NEW GCLIENT` / disconnects.

Apply this minimal local fix in `external/ZAPPY_GC/Scripts/StartButton.gd` if the GUI does not stay in the 3D scene:

```gdscript
extends Button

const MAIN_MENU_SCENE := "res://Scenes/MainMenuUI.tscn"

@onready var Port = $"../Port"
@onready var Host = $"../Host"

var portNumber = "4242"
var hostString = "127.0.0.1"

func _ready() -> void:
	if not _is_root_main_menu():
		return
	await get_tree().process_frame
	_on_pressed()

func _is_root_main_menu() -> bool:
	var current_scene := get_tree().current_scene
	return current_scene != null and current_scene.scene_file_path == MAIN_MENU_SCENE
```

Keep the existing `_on_pressed()` body after that. Healthy startup should show exactly one GUI connection:

```bash
rg -c "Connected to server\\." .local/demo/gui.log
rg -c "NEW GCLIENT" .local/demo/server.log
```

Both should print `1`.

## One-Command Visual Demo

Install the AI package and verify paths:

```bash
make demo-preflight
make demo-ai-install
```

Run the full local demo:

```bash
make demo-full
```

Defaults:

- Server host/port: `127.0.0.1:4242`
- Team: `pollo`
- Map: `10x10`
- Tick rate: `100`
- Initial server slots: `4`
- AI processes launched: `16`
- Logs: `.local/demo`

The server starts with 4 initial slots on purpose. The other 12 AI clients connect and wait in the handshake path until egg/fork mechanics open capacity. Do not raise slots to 16 just to make all clients join immediately if you want to exercise real game mechanics.

Expected terminal output:

```text
Logs: /home/andres/zappy_ai/.local/demo
Starting server: port=4242 map=10x10 team=pollo slots=4 tick=100
Server ready.
Starting GUI with Godot: /home/andres/Godot/Godot_v4.6.1-stable_linux.x86_64
Waiting 4s for the GUI window to connect before launching agents...
Starting 16 AI clients for team pollo (4 initial slots; 12 bench clients wait for eggs)...
Demo running.
Server log: /home/andres/zappy_ai/.local/demo/server.log
GUI log: /home/andres/zappy_ai/.local/demo/gui.log
AI logs: /home/andres/zappy_ai/.local/demo/ai/ai-*.log
Stop with Ctrl+C.
```

Expected GUI result:

- Godot opens `Zappy_GC (DEBUG)`.
- Server status shows `online`.
- The 3D map is visible.
- Resource UI shows items such as `Food`, `Linemate`, `Mendiane`, `Phiras`, and `Sibur`.
- The first 4 players spawn from initial slots.
- More clients join later as active players fork and eggs hatch.

Stop with `Ctrl+C` in the `make demo-full` terminal.

## Headless Smoke Test

Use this to verify server, GUI connection, and AI startup without opening the visible window:

```bash
timeout 35s make demo-full GODOT_ARGS=--headless
```

`timeout` exits with `124`; that is expected.

Useful checks after a run:

```bash
rg -c "Connected to server\\." .local/demo/gui.log
rg -c "TilesX:" .local/demo/gui.log
rg -c "NEW GCLIENT" .local/demo/server.log
rg -c "Player with fd" .local/demo/server.log
ls -1 .local/demo/ai | wc -l
rg -c "EXECUTING FORK" .local/demo/server.log
```

Verified 4-slot behavior:

```text
Player with fd 5 assigned to id 0
Player with fd 6 assigned to id 1
Player with fd 7 assigned to id 2
Player with fd 8 assigned to id 3
EXECUTING FORK
...
Egg    from team pollo is eating
Player with fd 9 assigned to id 4
```

## Manual Component Commands

Start only the server:

```bash
make demo-server
```

Equivalent direct command:

```bash
./external/zappy/server -p 4242 -x 10 -y 10 -n pollo -c 4 -t 100
```

Start only the GUI:

```bash
make demo-gui
```

Equivalent direct command:

```bash
godot4 --path external/ZAPPY_GC
```

Start one AI:

```bash
make demo-ai
```

Equivalent direct command:

```bash
.venv/bin/python -m zappy_ai.client -h 127.0.0.1 -p 4242 -n pollo
```

Start 16 AIs manually:

```bash
mkdir -p .local/demo
for i in $(seq 1 16); do
  make demo-ai > ".local/demo/manual-ai-$i.log" 2>&1 &
done
```

## Protocol Summary

There is no direct AI-to-GUI connection. Both connect to the server over TCP.

AI handshake:

1. Server sends `BIENVENUE`.
2. AI sends team name, e.g. `pollo`.
3. Server replies with available slots.
4. When assigned, server sends map size, e.g. `10 10`.

GUI handshake:

1. GUI connects to `127.0.0.1:4242` by default.
2. GUI sends `GRAPHIC`.
3. Server streams graphic state such as `msz`, `sgt`, `bct`, `tna`, `pnw`, `ppo`, `pin`, `pgt`, and egg events.

## Troubleshooting

If Python imports fail:

```bash
. .venv/bin/activate
python -m pip install -e . --no-build-isolation
python -c "import zappy_ai; print(zappy_ai.__file__)"
```

If `numpy` is missing, reinstall from the AI repo root:

```bash
.venv/bin/python -m pip install -e . --no-build-isolation
```

If Godot is not found:

```bash
./scripts/find_godot.sh
GODOT_BIN="/path/to/godot" make demo-full
```

If port `4242` is already in use, prefer stopping the old demo/server because the GUI auto-connect default is also `4242`. Check for stale processes with:

```bash
ps -ef | rg 'demo_full|external/zappy/server|Godot|zappy_ai\\.client'
```

If you must use another port for `demo-full`, also change the GUI default in `external/ZAPPY_GC/Scripts/StartButton.gd` before launching:

```gdscript
var portNumber = "4243"
```

Then run:

```bash
make DEMO_PORT=4243 demo-full
```

For a manual GUI run on a non-default port, enter the new port in the GUI before connecting. The one-command `demo-full` path passes the port to server and AI, but the GUI project defaults to `4242` unless edited or driven through its menu.
