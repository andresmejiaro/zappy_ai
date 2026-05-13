# Zappy Demo Video Tools

This folder documents the local video pipeline used to render the AI-focused Zappy montage. Generated videos and replay files stay under `.local/` and are intentionally ignored by Git.

## What Is Included

- `scripts/demo_video.sh`: records the Godot window with `ffmpeg x11grab` at `1920x1080`, `30fps`, `libx264`.
- `scripts/render_zappy_ai_video.py`: builds a captioned montage from replayed protocol events.
- `docs/video/ZAPPY_GC-demo-video.patch`: patch for the ignored Godot GUI clone under `external/ZAPPY_GC`.
- `make demo-video`, `make demo-replay-video`, and `make demo-ai-video`: reusable entry points.

## Requirements

- Linux X11 or XWayland session with `DISPLAY` set.
- `ffmpeg`, `ffprobe`, `xwininfo`, `rg`, `fc-match`, and `timeout`.
- A working Godot binary discoverable by `scripts/find_godot.sh`.
- The C++ server built at `external/zappy/server` for live runs.
- The Python AI installed in `.venv` for live runs.

## Apply The Godot Patch

The root repo ignores `external/`, so the Godot demo/replay changes are stored as a patch.

From the root repo:

```bash
git -C external/ZAPPY_GC apply --check ../../docs/video/ZAPPY_GC-demo-video.patch
git -C external/ZAPPY_GC apply ../../docs/video/ZAPPY_GC-demo-video.patch
```

The patch adds:

- Demo window title: `Zappy Demo`.
- Deterministic demo camera presets.
- Hidden capture-irrelevant UI in demo mode.
- Protocol line normalization.
- JSONL protocol recording.
- Replay mode through `DEMO_REPLAY_FILE`.

## Record A Live Clip

```bash
make demo-video
```

Useful variables:

```bash
make demo-video \
  DEMO_VIDEO_SECONDS=20 \
  DEMO_VIDEO_WARMUP=8 \
  DEMO_VIDEO_OUT=.local/demo/video/my-live-clip.mp4
```

## Record A Replay Clip

First record protocol during a normal demo:

```bash
make demo-full DEMO_RECORD_PROTOCOL=1
```

Then render from the JSONL replay:

```bash
make demo-replay-video \
  DEMO_REPLAY_FILE=.local/demo/replay/protocol-example.jsonl \
  DEMO_VIDEO_OUT=.local/demo/video/my-replay-clip.mp4
```

Replay mode skips the C++ server and Python clients. It feeds recorded protocol lines back through the Godot GUI.

## Render The AI Montage

```bash
make demo-ai-video \
  DEMO_REPLAY_FILE=.local/demo/replay/protocol-example.jsonl \
  DEMO_MONTAGE_OUT=.local/demo/video/my-ai-montage.mp4
```

Audio is optional. If the default local tracks are missing, the script renders a silent montage. To use explicit tracks, pass a colon-separated list:

```bash
make demo-ai-video \
  DEMO_REPLAY_FILE=.local/demo/replay/protocol-example.jsonl \
  DEMO_MONTAGE_AUDIO_FILES="/path/song-a.mp3:/path/song-b.mp3"
```

## Customize A Teammate Video

Edit `build_segments()` in `scripts/render_zappy_ai_video.py`.

- Use `CardSegment` for title/structure/end cards.
- Use `ClipSegment` for gameplay clips with captions.
- Set `start_s` and `duration_s` to choose replay moments.
- Set `focus=(x, y)` to point the camera at a map tile.
- Set `preset` to one of: `overview`, `medium`, `medium_alt`, `topdown`, `low`, `low_alt`, `queen`, `queen_alt`, `dense`, `dense_alt`.

For a C++ server or Godot GUI video, keep the same capture pipeline and replace the storyboard/captions.

## Outputs

- Videos: `.local/demo/video/`
- Replay logs: `.local/demo/replay/`
- Montage workspaces: `.local/demo/montage/`
- Capture logs: `.local/demo/montage/<timestamp>/capture-logs/`

## Commit Guidance

Commit the scripts, Makefile changes, this README, and the Godot patch. Do not commit `.local/` outputs unless the team explicitly wants binary video files in Git.
