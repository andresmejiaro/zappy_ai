# Local Visual Demo Runbook

Goal: run one local visual demo where the C++ server starts, the Godot GUI connects, 16 Python AI clients connect, and movement/resource/game state is visible in the GUI.

## Defaults

- Server: `external/zappy/server`
- GUI: `external/ZAPPY_GC` via Godot
- AI: root Python package `zappy_ai`
- Host: `127.0.0.1`
- Port: `4242`
- Team: `pollo`
- Map: `10x10`
- AI clients: `16`
- Initial server slots: `4`
- Tick rate: `100`
- Logs: `.local/demo`

These defaults match the GUI auto-connect path. The launcher starts 16 AI processes, but the server starts with 4 initial slots; the other 12 clients wait in handshake until egg/fork mechanics open capacity.

## One-Time Setup

Run:

```bash
make demo-preflight
make demo-ai-install
```

Expected preflight output on this machine:

```text
Server binary: /home/andres/zappy_ai/external/zappy/server
Python: /home/andres/zappy_ai/.venv/bin/python
Python 3.13.7
Godot: /home/andres/Godot/Godot_v4.6.1-stable_linux.x86_64
4.6.1.stable.official.14d19694e
```

Expected AI install output:

```text
Obtaining file:///home/andres/zappy_ai
Requirement already satisfied: numpy in ./.venv/lib/python3.13/site-packages ...
Successfully installed zappy_ai-0.0.0
```

## Full Visual Demo

Run:

```bash
make demo-full
```

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

Expected visible result:

- Godot opens a `Zappy_GC (DEBUG)` window.
- The server status in the GUI shows `online`.
- The 3D island/map is visible instead of the title screen.
- The right-side resource panel shows resources such as `Food`, `Linemate`, `Mendiane`, `Phiras`, and `Sibur`.
- The first 4 players appear from the initial slots; additional clients join as eggs are laid and hatch.
- Game state updates continue as active AI clients act.

Stop the demo with `Ctrl+C` in the terminal running `make demo-full`.

## Verified Log Checks

After `make demo-full` has been running for a few seconds, these checks should match the successful run:

```bash
rg -c "Connected to server\\." .local/demo/gui.log
rg -c "TilesX:" .local/demo/gui.log
rg -c "NEW GCLIENT" .local/demo/server.log
rg -c "Player with fd" .local/demo/server.log
ls -1 .local/demo/ai | wc -l
rg -c "EXECUTING FORK" .local/demo/server.log
rg -c "EXECUTING AVANCE|EXECUTING PREND|EXECUTING INVENTAIRE|EXECUTING BROADCAST|EXECUTING FORK" .local/demo/server.log
```

Observed values from the 4-slot headless verification run:

```text
1
1
1
16
16
19
3542
```

The `Player with fd` count may start at `4` and increase as forked eggs become available. In the verification run, all 16 clients eventually joined because the active agents forked quickly. The activity counts are run-duration dependent and should keep increasing while the demo runs.

The important startup ordering is that only 4 players are assigned before fork events:

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

Useful live output samples:

```text
Received in network: ppo 13 7 4 2
pgt 7 6
pin 7 6 4 14 0 0 0 0 0 1
bct 6 4 0 29 16 9 1 1 17
```

```text
Player with fd 20 assigned to id 15
EXECUTING AVANCE
EXECUTING PREND
EXECUTING INVENTAIRE
```

## Headless Smoke Test

Use this when you want to verify startup without opening a visible window:

```bash
timeout 30s make demo-full GODOT_ARGS=--headless
```

Expected output before `timeout` stops the demo:

```text
Logs: /home/andres/zappy_ai/.local/demo
Starting server: port=4242 map=10x10 team=pollo slots=4 tick=100
Server ready.
Starting GUI with Godot: /home/andres/Godot/Godot_v4.6.1-stable_linux.x86_64
GUI connected in headless verification mode.
Starting 16 AI clients for team pollo (4 initial slots; 12 bench clients wait for eggs)...
Demo running.
Server log: /home/andres/zappy_ai/.local/demo/server.log
GUI log: /home/andres/zappy_ai/.local/demo/gui.log
AI logs: /home/andres/zappy_ai/.local/demo/ai/ai-*.log
Stop with Ctrl+C.

Stopping demo processes...
```

An exit code of `124` is expected when `timeout` ends the process.

## Optional Manual Flow

The one-command flow is preferred. If you need separate terminals:

Terminal 1:

```bash
make demo-server
```

Terminal 2:

```bash
make demo-gui
```

Terminal 3:

```bash
for i in $(seq 1 16); do make demo-ai > ".local/demo/manual-ai-$i.log" 2>&1 & done
```

Expected server output includes:

```text
Server listening on port 4242
NEW GCLIENT WITH FD:4
Player with fd ... assigned to id 0
...
Player with fd ... assigned to id 15
```

## Useful Overrides

Examples:

```bash
make DEMO_AGENTS=20 demo-full
make DEMO_SLOTS=8 DEMO_AGENTS=20 demo-full
make DEMO_WIDTH=20 DEMO_HEIGHT=20 demo-full
make DEMO_PORT=4243 demo-server
make GODOT_BIN="$HOME/Godot/Godot_v4.6.1-stable_linux.x86_64" demo-gui
make demo-gui GODOT_ARGS=--version
```

If you change `DEMO_PORT` for the full demo, all components receive the same port through the script. If you use the manual flow with a non-default port, enter that port in the GUI before connecting or keep `4242`.

## Troubleshooting

If Godot is not found:

```bash
./scripts/find_godot.sh
```

Expected result on this machine:

```text
/home/andres/Godot/Godot_v4.6.1-stable_linux.x86_64
```

If the GUI shows only the title screen, check for the old reconnect-loop symptom:

```bash
rg -c "Connected to server\\." .local/demo/gui.log
rg -c "NEW GCLIENT" .local/demo/server.log
```

Both should be `1` during a healthy startup. Large values mean the GUI is reconnecting instead of staying in the game scene.

If the AI import fails:

```bash
make demo-ai-install
```

If the server reports that port `4242` is already in use, stop the old demo or use:

```bash
make DEMO_PORT=4243 demo-full
```
